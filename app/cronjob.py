# -*- coding: utf-8 -*-
import binascii
import sys

from app import log, config

from app.model import Didtx, Servicecount
from app.model import Didstate

from app.service import DidPublish

LOG = log.get_logger()

did_publish = DidPublish()


def reset_didpublish_daily_limit():
    rows = Servicecount.objects()
    for row in rows:
        if config.SERVICE_DIDPUBLISH in row.data.keys():
            did_txs = Didtx.objects()
            result = {}
            for tx in did_txs:
                if tx.did in result.keys():
                    result[tx.did] += 1
                else:
                    result[tx.did] = 1
            row.data["did_publish"] = {
                "count": 0,
                "total_count": result[row.did]
            }
            row.save()


def send_tx_to_did_sidechain():
    # Verify the DID sidechain is reachable
    response = did_publish.get_block_count()
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
    try:
        # Create raw transactions
        rows_pending = Didtx.objects(status=config.SERVICE_STATUS_PENDING)
        for row in rows_pending:
            tx = did_publish.create_raw_transaction(row.did, row.didRequest)
            if not tx:
                return
            tx_decoded = binascii.hexlify(tx).decode(encoding="utf-8")
            pending_transactions.append(tx_decoded)

        if pending_transactions:
            LOG.info("Pending: Found transactions. Sending " + str(len(pending_transactions)) + " transactions to DID "
                                                                                                "sidechain now...")
            # Send transaction to DID sidechain
            response = did_publish.send_raw_transaction(pending_transactions)
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
                row.save()

        # Get info about all the transactions and save them to the database
        rows_processing = Didtx.objects(status=config.SERVICE_STATUS_PROCESSING)
        for row in rows_processing:
            blockchain_tx = did_publish.get_raw_transaction(row.blockchainTxId)
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
        rows_quarantined = Didtx.objects(status=config.SERVICE_STATUS_QUARANTINE)
        for row in rows_quarantined:
            LOG.info(
                "Quarantine: Trying to re-send quarantined transaction for id: " + str(row.id) + " DID: " + row.did)
            did_publish.current_wallet_index += 1
            if did_publish.current_wallet_index > config.NUM_WALLETS - 1:
                did_publish.current_wallet_index = 0
            # Try sending each transaction one by one
            tx = did_publish.create_raw_transaction(row.did, row.didRequest)
            tx_decoded = binascii.hexlify(tx).decode(encoding="utf-8")
            response = did_publish.send_raw_transaction([tx_decoded])
            tx_id = response["result"]
            if tx_id:
                row.status = config.SERVICE_STATUS_PROCESSING
                row.blockchainTxId = tx_id
                row.extraInfo = ''
                LOG.info("Quarantine: Successfully sent quarantined transaction from wallet: " +
                         did_publish.wallets[did_publish.current_wallet_index]["address"] + " for id: " + str(row.id) + " DID: " + row.did)
                break
            else:
                row.extraInfo = response["error"]
                LOG.info("Quarantine: Error sending transaction from wallet: " +
                         did_publish.wallets[did_publish.current_wallet_index]["address"] + " for id:" + str(
                    row.id) + " DID:" + row.did + " Error: " + str(row.extraInfo))
            row.save()
    except Exception as err:
        message = "Error: " + str(err) + "\n"
        exc_type, exc_obj, exc_tb = sys.exc_info()
        message += "Unexpected error: " + str(exc_type) + "\n"
        message += ' File "' + exc_tb.tb_frame.f_code.co_filename + '", line ' + str(exc_tb.tb_lineno) + "\n"
        LOG.info(f"Error while running cron job: {message}")

