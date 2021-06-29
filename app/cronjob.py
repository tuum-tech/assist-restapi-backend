# -*- coding: utf-8 -*-
import binascii
import itertools
import sys
import json
from datetime import datetime

from pymongo import MongoClient

from app import log, config

from app.model import Didtx, DidDocument, Servicecount
from app.model import Didstate

from app.service import DidPublish, DidSidechainRpc, get_service_count, get_didtx_count, send_email, \
    send_slack_notification

LOG = log.get_logger()

did_publish = DidPublish()
did_sidechain_rpc = DidSidechainRpc()


def cron_send_tx_to_did_sidechain():
    LOG.info('Started cron job: send_tx_to_did_sidechain')
    # Verify the DID sidechain is reachable
    response = did_sidechain_rpc.get_block_count()
    if not (response and response["result"]):
        LOG.info("DID sidechain is currently not reachable...")
        return

    current_height = response["result"] - 1
    # Retrieve the current height from the database
    rows = Didstate.objects()
    if rows:
        row = rows[0]
        # Verify whether a new block has been added since last time
        if current_height > row.currentHeight:
            row.currentHeight = current_height
            row.save()
        else:
            LOG.info("There hasn't been any new block since last cron job was run...")
            return
    else:
        row = Didstate(currentHeight=current_height)
        row.save()

    pending_transactions = []
    current_time = datetime.utcnow().strftime("%a, %b %d, %Y @ %I:%M:%S %p")
    slack_blocks = [
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": ""
            }
        },
        {
            "type": "divider"
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": ""
            }
        },
        {
            "type": "divider"
        }
    ]
    try:
        # Create raw transactions
        rows_pending = Didtx.objects(status=config.SERVICE_STATUS_PENDING, version="1")
        for row in rows_pending:
            time_since_created = datetime.utcnow() - row.created
            if (time_since_created.total_seconds() / 60.0) > 60:
                LOG.info(
                    f"The id '{row.id}' with DID '{row.did}' has been in Pending state for the last hour. Changing "
                    f"its state to Cancelled")
                row.status = config.SERVICE_STATUS_CANCELLED
                row.extraInfo = {
                    "reason": "Was in pending state for more than 1 hour"
                }
                row.save()
                continue
            tx = did_publish.create_raw_transaction(row.did, row.didRequest)
            if not tx:
                continue
            tx_decoded = binascii.hexlify(tx).decode(encoding="utf-8")
            pending_transactions.append(tx_decoded)

        if pending_transactions:
            LOG.info("Pending: Found transactions. Sending " + str(len(pending_transactions)) + " transactions to DID "
                                                                                                "sidechain now...")
            # Send transaction to DID sidechain
            response = did_sidechain_rpc.send_raw_transaction(pending_transactions)
            if not response:
                return
            tx_id = response["result"]
            for row in rows_pending:
                # If for whatever reason, the transactions fail, put them in quarantine and come back to it later
                if tx_id:
                    row.status = config.SERVICE_STATUS_PROCESSING
                    row.blockchainTxId = tx_id
                    LOG.info("Pending: Successfully sent transaction from wallet: " +
                             did_publish.wallets[did_publish.current_wallet_index][
                                 "address"] + " to the blockchain for id: " + str(
                        row.id) + " DID: " + row.did + " tx_id: " + tx_id)
                else:
                    row.extraInfo = response["error"]
                    row.status = config.SERVICE_STATUS_QUARANTINE
                    LOG.info("Pending: Error sending transaction from wallet: " +
                             did_publish.wallets[did_publish.current_wallet_index]["address"] + " for id: " + str(
                        row.id) + " DID:" + row.did + " Error: " + str(row.extraInfo))
                    slack_blocks[0]["text"]["text"] = f"The following transaction was sent to quarantine at {current_time}"
                    slack_blocks[2]["text"]["text"] = f"Wallet used: {did_publish.wallets[did_publish.current_wallet_index]['address']}\n" \
                                                      f"Transaction ID: {str(row.id)}\n"  \
                                                      f"DID: {row.did}\n"  \
                                                      f"Error: {str(row.extraInfo)}"
                    send_slack_notification(slack_blocks)
                row.save()

        # Get info about all the transactions and save them to the database
        rows_processing = Didtx.objects(status=config.SERVICE_STATUS_PROCESSING, version="1")
        for row in rows_processing:
            blockchain_tx = did_sidechain_rpc.get_raw_transaction(row.blockchainTxId)
            row.blockchainTx = blockchain_tx
            LOG.info("Processing: Blockchain transaction info from wallet: " +
                     did_publish.wallets[did_publish.current_wallet_index]["address"] + " for id: " + str(
                row.id) + " DID:" + row.did)
            if blockchain_tx["result"]:
                confirmations = blockchain_tx["result"]["confirmations"]
                if confirmations > 2 and row.status != config.SERVICE_STATUS_COMPLETED:
                    row.status = config.SERVICE_STATUS_COMPLETED
                    row.blockchainTx["result"]["confirmations"] = "2+"
            row.save()

        # Try to process quarantined transactions one at a time
        rows_quarantined = Didtx.objects(status=config.SERVICE_STATUS_QUARANTINE, version="1")
        binary_split_resend(rows_quarantined)
    except Exception as err:
        message = "Error: " + str(err) + "\n"
        exc_type, exc_obj, exc_tb = sys.exc_info()
        message += "Unexpected error: " + str(exc_type) + "\n"
        message += ' File "' + exc_tb.tb_frame.f_code.co_filename + '", line ' + str(exc_tb.tb_lineno) + "\n"
        slack_blocks[0]["text"]["text"] = f"Error while sending tx to the blockchain at {current_time}"
        slack_blocks[2]["text"]["text"] = f"Wallet used: {did_publish.wallets[did_publish.current_wallet_index]['address']}\n" \
                                          f"Error: {message}"
        send_slack_notification(slack_blocks)
        LOG.info(f"Error while running cron job: {message}")
    LOG.info('Completed cron job: send_tx_to_did_sidechain')


def binary_split_resend(rows_quarantined):
    for row in rows_quarantined:
        LOG.info("Binary split start: rows: " + str(row.modified))

    # Split quarantined transactions into 2 sets and process each set one at a time
    LOG.info("Binary split of " + str(len(rows_quarantined)) + " quarantined transactions")

    # first create raw transactions for each
    q_transactions = []
    for row in rows_quarantined:
        tx = did_publish.create_raw_transaction(row.did, row.didRequest)
        if not tx:
            return
        tx_decoded = binascii.hexlify(tx).decode(encoding="utf-8")
        q_transactions.append(tx_decoded)

    # second submit 1/2 transactions then the other half
    # Send transaction to DID sidechain
    start = 0
    stop = 0
    for x in [0, 1]:
        if x == 0:
            start = 0
            stop = round(len(rows_quarantined) / 2)
            q_half_array = q_transactions[:round(len(rows_quarantined) / 2)]
            LOG.info("Binary split in pass: " + str(x) + " from 0 to " + str(
                round(len(rows_quarantined) / 2)) + " total array length: " + str(len(rows_quarantined)))
        else:
            start = round(len(q_transactions) / 2)
            stop = len(q_transactions)
            q_half_array = q_transactions[round(len(rows_quarantined) / 2):]
            LOG.info(
                "Binary split in pass: " + str(x) + " from " + str(round(len(rows_quarantined) / 2)) + " to " + str(
                    len(rows_quarantined)) + " total array length: " + str(len(rows_quarantined)))

        response = did_sidechain_rpc.send_raw_transaction(q_half_array)
        if not response:
            return
        tx_id = response["result"]
        if tx_id:
            # If transactions are good set the status to "Processing"
            # use itertools to pull back proper part of the original database rows collection
            for row in itertools.islice(rows_quarantined, start, stop):
                row.status = config.SERVICE_STATUS_PROCESSING
                row.blockchainTxId = tx_id
                LOG.info("Binary Split: Successfully sent transaction from wallet: " +
                         did_publish.wallets[did_publish.current_wallet_index][
                             "address"] + " to the blockchain for id: " + str(
                    row.id) + " DID: " + row.did + " tx_id: " + tx_id)
                row.save()
        else:
            # If the transaction failed, make sure to switch to a different wallet
            did_publish.current_wallet_index += 1
            if did_publish.current_wallet_index > config.NUM_WALLETS - 1:
                did_publish.current_wallet_index = 0
            # if part of batch fails split send it separately
            subset_of_rows = rows_quarantined[slice(start, stop)]
            LOG.info("Binary split failed: on pass: " + str(x) + " start: " + str(start) + " stop: " + str(
                stop) + " length: " + str(len(subset_of_rows)) + " of original: " + str(len(rows_quarantined)))

            if len(subset_of_rows) >= 2:
                LOG.info("Binary split IF:  start " + str(start) + " stop: " + str(stop) + " length: " + str(
                    len(subset_of_rows)))
                for row in subset_of_rows:
                    LOG.info("Binary split failed: rows: " + str(row.modified))
                binary_split_resend(subset_of_rows)
