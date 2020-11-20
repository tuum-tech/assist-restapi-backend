# -*- coding: utf-8 -*-
import binascii
import itertools
import sys
import json
from datetime import datetime

from app import log, config

from app.model import Didtx, DidDocument, Servicecount
from app.model import Didstate

from app.service import DidPublish, DidSidechainRpc, get_service_count, get_didtx_count, send_email, \
    send_slack_notification

LOG = log.get_logger()

did_publish = DidPublish()
did_sidechain_rpc = DidSidechainRpc()


def cron_send_daily_stats():
    LOG.info('Started cron job: cron_send_daily_stats')
    to_email = config.EMAIL["SENDER"]
    subject = "Assist Backend Daily Stats"

    current_time = datetime.utcnow().strftime("%a, %b %d, %Y @ %I:%M:%S %p")
    slack_blocks = [
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"These are the daily stats for Assist for {current_time}"
            }
        },
        {
            "type": "divider"
        }
    ]

    wallets_stats = "<table><tr><th>Address</th><th>Balance</th><th>Type</th></tr>"
    # Used for testing purposes
    test_address = "EKsSQae7goc5oGGxwvgbUxkMsiQhC9ZfJ3"
    test_balance = did_sidechain_rpc.get_balance(test_address)
    wallets_stats += f"<tr><td>{test_address}</td><td>{test_balance}</td><td>Testing</td></tr>"
    slack_blocks.append({
        "type": "section",
        "text": {
            "type": "mrkdwn",
            "text": f"*Wallets and Current Balances*\n {test_address} | {test_balance} | Testing\n"
        }
    })
    for wallet in config.WALLETS:
        address = wallet["address"]
        balance = did_sidechain_rpc.get_balance(address)
        wallets_stats += f"<tr><td>{address}</td><td>{balance}</td><td>Production</td></tr>"
        slack_blocks[2]["text"]["text"] += f"{address} | {balance} | Production\n"
    wallets_stats += "</table>"

    service_stats = "<table><tr><th>Service</th><th>Users</th><th>Today</th><th>All time</th></tr>"
    slack_blocks.append({
        "type": "section",
        "text": {
            "type": "mrkdwn",
            "text": f"*Service Stats*\n"
        }
    })
    for service, stats in get_service_count().items():
        service_stats += f"<tr><td>{service}</td><td>{stats['users']}</td><td>{stats['today']}</td><td>{stats['total']}</td></tr>"
        slack_blocks[3]["text"][
            "text"] += f"{service} | {stats['users']} total users | {stats['today']} tx today | {stats['total']} tx total\n"
    service_stats += "</table>"

    didtx_stats = "<table><tr><th>Application</th><th>Today</th><th>All time</th></tr>"
    slack_blocks.append({
        "type": "section",
        "text": {
            "type": "mrkdwn",
            "text": f"*DID Transactions*\n"
        }
    })
    didtx_by_app = get_didtx_count()
    for app in didtx_by_app["total"].keys():
        didtx_stats += f"<tr><td>{app}</td><td>{didtx_by_app['today'].get(app, 0)}</td><td>{didtx_by_app['total'].get(app, 0)}</td></tr>"
        slack_blocks[4]["text"][
            "text"] += f"{app} | {didtx_by_app['today'].get(app, 0)} tx today | {didtx_by_app['total'].get(app, 0)} tx total\n"
    didtx_stats += "</table>"

    quarantined_transactions = "<table><tr><th>Transaction ID</th><th>DID</th><th>From</th><th>Extra " \
                               "Info</th><th>Created</th></tr>"
    slack_blocks.append({
        "type": "section",
        "text": {
            "type": "mrkdwn",
            "text": f"*Quarantined Transactions*\n"
        }
    })
    for transaction in Didtx.objects(status=config.SERVICE_STATUS_QUARANTINE):
        id = transaction.id
        did = transaction.did
        request_from = transaction.requestFrom
        created = transaction.created
        extra_info = json.dumps(transaction.extraInfo)
        quarantined_transactions += f"<tr><td>{id}</td><td>{did}</td><td>{request_from}</td><td>{extra_info}</td><td>{created}</td></tr>"
        slack_blocks[5]["text"]["text"] += f"{id} | {did} | {request_from} | {extra_info} | {created}\n"
    quarantined_transactions += "</table>"

    stale_processing_transactions = "<table><tr><th>Transaction ID</th><th>DID</th><th>From</th><th>Extra " \
                                    "Info</th><th>Created</th></tr>"
    slack_blocks.append({
        "type": "section",
        "text": {
            "type": "mrkdwn",
            "text": f"*Stale Processing Transactions(Over 1 hour)*\n"
        }
    })
    for transaction in Didtx.objects(status=config.SERVICE_STATUS_PROCESSING):
        time_since_created = datetime.utcnow() - transaction.created
        if (time_since_created.total_seconds() / 60.0) > 60:
            id = transaction.id
            did = transaction.did
            request_from = transaction.requestFrom
            created = transaction.created
            extra_info = json.dumps(transaction.extraInfo)
            stale_processing_transactions += f"<tr><td>{id}</td><td>{did}</td><td>{request_from}</td><td>{extra_info}</td><td>{created}</td></tr>"
            slack_blocks[6]["text"]["text"] += f"{id} | {did} | {request_from} | {extra_info} | {created}\n"
    stale_processing_transactions += "</table>"
    slack_blocks.append({
        "type": "divider"
    })

    content_html = f"""
        <html>
        <head>
            <style>
            table {{
              font-family: arial, sans-serif;
              border-collapse: collapse;
              width: 100%;
            }}
            
            td, th {{
              border: 1px solid #dddddd;
              text-align: left;
              padding: 8px;
            }}
            
            tr:nth-child(even) {{
              background-color: #dddddd;
            }}
            </style>
        </head>
        <body>
            <h2>These are the daily stats for Assist for {current_time}</h1>
            <h3>Wallets and Current Balances</h3>
            {wallets_stats}
            <h3>Service Stats</h3>
            {service_stats}
            <h3>DID Transactions</h3>
            {didtx_stats}
            <h3>Quarantined Transactions</h3>
            {quarantined_transactions}
            <h3>Stale Processing Transactions(Over 1 hour)</h3>
            {stale_processing_transactions}
        </body>
        </html>
    """
    send_email(to_email, subject, content_html)
    send_slack_notification(slack_blocks)
    cron_reset_didpublish_daily_limit()
    LOG.info('Completed cron job: cron_send_daily_stats')


def cron_reset_didpublish_daily_limit():
    LOG.info('Started cron job: reset_didpublish_daily_limit')
    rows = Servicecount.objects()
    for row in rows:
        if config.SERVICE_DIDPUBLISH in row.data.keys():
            did_txs = Didtx.objects(did=row.did)
            if did_txs:
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
    LOG.info('Completed cron job: reset_didpublish_daily_limit')


def cron_update_recent_did_documents():
    LOG.info('Started cron job: update_recent_did_documents')
    rows = DidDocument.objects()
    for row in rows:
        time_since_last_searched = datetime.utcnow() - row.last_searched
        # Remove DIDs from the database that no one has searched for the last 90 days
        if (time_since_last_searched.total_seconds() / (60.0 * 60.0 * 24.0)) > 90:
            LOG.info(f"The DID '{row.did}' has not been searched for the last 90 days. Removing from the database to "
                     f"save some space")
            row.delete()
        else:
            row.documents = did_sidechain_rpc.get_documents_specific_did(row.did)
            row.save()
    LOG.info('Completed cron job: update_recent_did_documents')


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
        rows_pending = Didtx.objects(status=config.SERVICE_STATUS_PENDING)
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
        rows_processing = Didtx.objects(status=config.SERVICE_STATUS_PROCESSING)
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
        rows_quarantined = Didtx.objects(status=config.SERVICE_STATUS_QUARANTINE)
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
