# -*- coding: utf-8 -*-
import sys
import json
from datetime import datetime
from pymongo import MongoClient
import multiprocessing

from app import log, config

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
    test_address = "0x365b70f14e10b02bef7e463eca6aa3e75ca3cdb1"
    test_balance = "{:.4f}".format(did_sidechain_rpc.get_balance(test_address))
    wallets_stats += f"<tr><td>{test_address}</td><td>{test_balance}</td><td>Testing</td></tr>"
    slack_blocks.append({
        "type": "section",
        "text": {
            "type": "mrkdwn",
            "text": f"*Wallets and Current Balances*\n {test_address} | {test_balance} | Testing\n"
        }
    })
    for wallet in config.WALLETSV2:
        address = json.loads(wallet)["address"]
        balance = "{:.4f}".format(did_sidechain_rpc.get_balance(f"0x{address}"))
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
        </body>
        </html>
    """
    if config.PRODUCTION:
        send_email(to_email, subject, content_html)
        send_slack_notification(slack_blocks)
    cron_reset_didpublish_daily_limit()
    LOG.info('Completed cron job: cron_send_daily_stats')


def cron_reset_didpublish_daily_limit():
    LOG.info('Started cron job: reset_didpublish_daily_limit')
    mongo_client = MongoClient(config.MONGO_CONNECT_HOST)
    db = mongo_client.assistdb

    result = db.servicecount.aggregate([
        {"$match": {"data.did_publish.count": {"$gt": 0}}},
        {"$group": {"_id": "$did"}},
        {"$project": {"_id": 0, "did": "$_id"}}
    ])

    for r in result:
        rows = Servicecount.objects(did=r["did"])
        row = rows[0]
        if config.SERVICE_DIDPUBLISH in row.data.keys():
            row.data["did_publish"]["count"] = 0
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


def cron_send_tx_to_did_sidechain_v2():
    LOG.info('Started cron job: cron_send_tx_to_did_sidechain_v2')
    try:
        # Verify the DID sidechain is reachable
        response = did_sidechain_rpc.get_block_count()
        if not response:
            LOG.info("DID sidechain is currently not reachable...")
            return

        rows_pending = Didtx.objects(status=config.SERVICE_STATUS_PENDING, version='2')
        rows_processing = Didtx.objects(status=config.SERVICE_STATUS_PROCESSING, version='2')
        LOG.info(f"rows pending {len(rows_pending)}")

        current_height = response - 1
        # Retrieve the current height from the database
        rows = Didstate.objects()
        if rows:
            row = rows[0]
            # Verify whether a new block has been added since last time
            if current_height > row.currentHeightv2:
                if len(rows_pending) == 0 and len(rows_processing) == 0:
                    LOG.info('Completed cron job: send_tx_to_did_sidechain_v2')
                    return
                row.currentHeightv2 = current_height
                row.save()
            else:
                LOG.info("There hasn't been any new block since last cron job was run...")
                return
        else:
            row = Didstate(currentHeight=0, currentHeightv2=0)
            row.save()
            return

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

        # Create raw transactions
        if len(rows_pending) > config.NUM_WALLETSV2:
            rows_pending = rows_pending[:config.NUM_WALLETSV2]
        wallets = config.WALLETSV2

        for index, row in enumerate(list(rows_pending)):
            process_pending_tx(wallets[index], row, slack_blocks, current_time)

        rows_processing = Didtx.objects(status=config.SERVICE_STATUS_PROCESSING, version='2')
        pool = multiprocessing.Pool()
        for row in rows_processing:
            #process_processing_tx(row, slack_blocks, current_time)
            pool.apply_async(process_processing_tx, args=(row, slack_blocks, current_time,))
        pool.close()
        pool.join()
        LOG.info('Completed cron job: send_tx_to_did_sidechain_v2')

    except Exception as err:
        message = "Error: " + str(err) + "\n"
        exc_type, exc_obj, exc_tb = sys.exc_info()
        message += "Unexpected error: " + str(exc_type) + "\n"
        message += ' File "' + exc_tb.tb_frame.f_code.co_filename + '", line ' + str(exc_tb.tb_lineno) + "\n"
        LOG.info(f"Error while running cron job: {message}")
        slack_blocks[0]["text"]["text"] = f"Error while sending tx to the blockchain at {current_time}"
        slack_blocks[2]["text"]["text"] = f"Error: {message}"
        send_slack_notification(slack_blocks)


def process_pending_tx(wallet, row, slack_blocks, current_time):
    address = json.loads(wallet)["address"]

    nonce = web3_did.increment_nonce(address)
    tx, err_message = web3_did.create_transaction(wallet, nonce, row.didRequest)
    if err_message:
        err_message = f"Could not generate a valid transaction out of the given didRequest. Error Message: {err_message}"
        LOG.info(f"Error: {err_message}")
        row.status = config.SERVICE_STATUS_REJECTED
        row.extraInfo = {"error": err_message}
        row.save()
        slack_blocks[0]["text"][
            "text"] = f"The following transaction was rejected at {current_time}"
        slack_blocks[2]["text"]["text"] = f"Wallet used: 0x{address}\n" \
                                          f"Transaction ID: {str(row.id)}\n" \
                                          f"DID: {row.did}\n" \
                                          f"Error: {str(row.extraInfo)}"
        send_slack_notification(slack_blocks)
        return
    LOG.info(f"Wallet 0x{address} used to create tx for id {row.id}")

    tx_response = did_sidechain_rpc.send_raw_transaction(tx)
    if tx_response["error"]:
        row.extraInfo = {"error": tx_response["error"]}
        row.status = config.SERVICE_STATUS_REJECTED
        row.save()
        LOG.info("Pending: Error sending transaction from wallet: 0x" +
                 address + " for id: " + str(row.id) + " DID:" + row.did +
                 " Error: " + str(row.extraInfo))
        slack_blocks[0]["text"][
            "text"] = f"The following transaction was rejected at {current_time}"
        slack_blocks[2]["text"]["text"] = f"Wallet used: 0x{address}\n" \
                                          f"Transaction ID: {str(row.id)}\n" \
                                          f"DID: {row.did}\n" \
                                          f"Error: {str(row.extraInfo)}"
        send_slack_notification(slack_blocks)
        return
    row.blockchainTxId = tx_response["tx_id"]
    row.status = config.SERVICE_STATUS_PROCESSING
    row.save()


def process_processing_tx(row, slack_blocks, current_time):
    time_since_created = datetime.utcnow() - row.created
    if (time_since_created.total_seconds() / 60.0) > 60:
        LOG.info(
            f"The id '{row.id}' with DID '{row.did}' has been in Pending/Processing state for the last hour. "
            f"Changing its state to Cancelled")
        row.status = config.SERVICE_STATUS_CANCELLED
        row.extraInfo = {
            "error": "Was in pending state for more than 1 hour"
        }
        row.save()
        slack_blocks[0]["text"][
            "text"] = f"The following transaction was cancelled at {current_time}"
        slack_blocks[2]["text"]["text"] = f"Transaction ID: {str(row.id)}\n" \
                                          f"DID: {row.did}\n" \
                                          f"Error: {str(row.extraInfo)}"
        send_slack_notification(slack_blocks)
        return

    result = did_sidechain_rpc.wait_for_transaction_receipt(row.blockchainTxId)
    tx_receipt, err_type, err_message = result["tx_receipt"], result["err_type"], result["err_message"]
    if tx_receipt:
        row.blockchainTx = tx_receipt
        if "status" in tx_receipt.keys() and tx_receipt["status"] == 1:
            row.status = config.SERVICE_STATUS_COMPLETED
            row.extraInfo = {}
            row.numTimeout = 0
        else:
            row.status = config.SERVICE_STATUS_REJECTED
            LOG.info("Pending: Error sending transaction:b" + " for id: " + str(row.id) + " DID:" + row.did +
                     " Error: " + str(row.extraInfo))
    else:
        row.extraInfo = {"error": err_message}
        if err_type == "TimeExhausted":
            if row.numTimeout > 5:
                row.status = config.SERVICE_STATUS_REJECTED
                row.save()
                LOG.info("Pending: Timeout while sending transaction: " +
                         " for id: " + str(row.id) + " DID:" + row.did +
                         " Error: " + str(row.extraInfo))
                slack_blocks[0]["text"][
                    "text"] = f"Due to the timeout, the following transaction was rejected at {current_time}"
                slack_blocks[2]["text"]["text"] = f"Transaction ID: {str(row.id)}\n" \
                                                  f"DID: {row.did}\n" \
                                                  f"Error: {str(row.extraInfo)}"
                send_slack_notification(slack_blocks)
            else:
                row.status = config.SERVICE_STATUS_PROCESSING
                row.numTimeout += 1
        else:
            row.status = config.SERVICE_STATUS_REJECTED
            row.save()
            LOG.info("Pending: Error sending transaction: " +
                     " for id: " + str(row.id) + " DID:" + row.did +
                     " Error: " + str(row.extraInfo))
            slack_blocks[0]["text"][
                "text"] = f"The following transaction was rejected at {current_time}"
            slack_blocks[2]["text"]["text"] = f"Transaction ID: {str(row.id)}\n" \
                                              f"DID: {row.did}\n" \
                                              f"Error: {str(row.extraInfo)}"
            send_slack_notification(slack_blocks)
    row.save()

