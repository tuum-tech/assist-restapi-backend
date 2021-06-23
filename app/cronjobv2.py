# -*- coding: utf-8 -*-
import sys
import json
from datetime import datetime

from app import log, config

from collections import deque

from app.model import Didtx, DidDocument, Servicecount
from app.model import Didstate

from app.service import Web3DidAdapter, DidSidechainRpcV2, get_service_count, get_didtx_count, send_email, \
    send_slack_notification

LOG = log.get_logger()

web3_did = Web3DidAdapter()
did_sidechain_rpc = DidSidechainRpcV2()


def cron_send_daily_stats_v2():
    LOG.info('Started cron job: cron_send_daily_stats_v2')
    to_email = config.EMAIL["SENDER"]
    subject = "Assist Backend Daily Stats V2"

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
    test_address = "0x365b70f14e10b02bef7e463eca6aa3e75ca3cdb1"
    test_balance = did_sidechain_rpc.get_balance(test_address)
    wallets_stats += f"<tr><td>{test_address}</td><td>{test_balance}</td><td>Testing</td></tr>"
    slack_blocks.append({
        "type": "section",
        "text": {
            "type": "mrkdwn",
            "text": f"*Wallets and Current Balances*\n {test_address} | {test_balance} | Testing\n"
        }
    })
    for wallet in config.WALLETSV2:
        address = json.loads(wallet["wallet"])["address"]
        balance = did_sidechain_rpc.get_balance(f"0x{address}")
        wallets_stats += f"<tr><td>0x{address}</td><td>{balance}</td><td>Production</td></tr>"
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

    for transaction in Didtx.objects(status=config.SERVICE_STATUS_QUARANTINE, version='2'):
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
    for transaction in Didtx.objects(status=config.SERVICE_STATUS_PROCESSING, version='2'):
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
    if config.PRODUCTION:
        send_email(to_email, subject, content_html)
        send_slack_notification(slack_blocks)
    LOG.info('Completed cron job: cron_send_daily_stats')


def cron_send_tx_to_did_sidechain_v2():
    LOG.info('Started cron job: cron_send_tx_to_did_sidechain_v2')
    # Verify the DID sidechain is reachable
    response = did_sidechain_rpc.get_block_count()
    if not response:
        LOG.info("DID sidechain is currently not reachable...")
        return

    current_height = response - 1
    # Retrieve the current height from the database
    rows = Didstate.objects()
    if rows:
        row = rows[0]
        # Verify whether a new block has been added since last time
        if current_height > row.currentHeightv2:
            row.currentHeightv2 = current_height
            row.save()
        else:
            LOG.info("There hasn't been any new block since last cron job was run...")
            return
    else:
        row = Didstate(currentHeight=0, currentHeightv2=current_height)
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
        didstate = Didstate.objects()[0]
        # Create raw transactions
        rows_pending = list(Didtx.objects(status=config.SERVICE_STATUS_PENDING, version='2'))
        LOG.info(f"rows pending {len(rows_pending)}")
        dequeueIndex = didstate.lastWalletUsed
        wallets = deque(config.WALLETSV2)
        if dequeueIndex < len(config.WALLETSV2):
           wallets.rotate(dequeueIndex * -1)
        for wallet in wallets:

            if len(rows_pending) == 0:
                continue

            row = rows_pending.pop()
            if not row:
                continue

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

            address = json.loads(wallet["wallet"])["address"]

            nonce = web3_did.increment_nonce(address)

            tx = web3_did.create_transaction(wallet["wallet"], nonce, row.didRequest)

            if not tx:
                continue

            didstate.lastWalletUsed = wallet["index"]
            didstate.save()

            LOG.info(f"Wallet no. '{wallet['index']}' used to create tx for id {row.id}")

            pending_transactions.append({
                "wallet_index": wallet["index"],
                "tx": tx
            })

        if pending_transactions:
            LOG.info("Pending: Found transactions. Sending " + str(len(pending_transactions)) + " transactions to DID "
                                                                                                "sidechain now...")

            # Send transaction to DID sidechain
            for pending_item in pending_transactions:
                used_wallet = json.loads(config.WALLETSV2[pending_item["wallet_index"] - 1]["wallet"])
                pending = pending_item["tx"]
                tx_response = did_sidechain_rpc.send_raw_transaction(pending)
                if not tx_response["error"]:
                    tx_id = tx_response["tx_id"]
                    row.status = config.SERVICE_STATUS_PROCESSING
                    row.blockchainTxId = tx_id
                    LOG.info("Pending: Successfully sent transaction from wallet: " +
                             used_wallet["address"] + " to the blockchain for id: " + str(
                        row.id) + " DID: " + row.did + " tx_id: " + tx_id)
                else:
                    row.extraInfo = tx_response["error"]
                    row.status = config.SERVICE_STATUS_QUARANTINE
                    LOG.info("Pending: Error sending transaction from wallet: " +
                             used_wallet["address"] + " for id: " + str(
                        row.id) + " DID:" + row.did + " Error: " + str(row.extraInfo))
                    slack_blocks[0]["text"][
                        "text"] = f"The following transaction was sent to quarantine at {current_time}"
                    slack_blocks[2]["text"]["text"] = f"Wallet used: {used_wallet['address']}\n" \
                                                      f"Transaction ID: {str(row.id)}\n" \
                                                      f"DID: {row.did}\n" \
                                                      f"Error: {str(row.extraInfo)}"
                    send_slack_notification(slack_blocks)
                row.save()

        # Get info about all the transactions and save them to the database
        rows_processing = Didtx.objects(status=config.SERVICE_STATUS_PROCESSING, version='2')
        for row in rows_processing:
            blockchain_tx = did_sidechain_rpc.get_raw_transaction(row.blockchainTxId)
            row.blockchainTx = blockchain_tx
            if blockchain_tx:
                if blockchain_tx["status"] == 1:
                    row.status = config.SERVICE_STATUS_COMPLETED
                else:
                    row.status = config.SERVICE_STATUS_REJECTED
            row.save()

        # Try to process quarantined transactions one at a time
        # TEMPORARY REMOVED
        # binary_split_resend(rows_quarantined)
    except Exception as err:
        message = "Error: " + str(err) + "\n"
        exc_type, exc_obj, exc_tb = sys.exc_info()
        message += "Unexpected error: " + str(exc_type) + "\n"
        message += ' File "' + exc_tb.tb_frame.f_code.co_filename + '", line ' + str(exc_tb.tb_lineno) + "\n"
        slack_blocks[0]["text"]["text"] = f"Error while sending tx to the blockchain at {current_time}"
        slack_blocks[2]["text"]["text"] = f"Wallet used: {web3_did.wallets[web3_did.current_wallet_index]['address']}\n" \
                                          f"Error: {message}"
        # send_slack_notification(slack_blocks)
        LOG.info(f"Error while running cron job: {message}")
    LOG.info('Completed cron job: send_tx_to_did_sidechain_v2')
