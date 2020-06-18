# -*- coding: utf-8 -*-
import binascii
import requests

import falcon
from apscheduler.schedulers.background import BackgroundScheduler

from falcon_cors import CORS

from app import log, config

from app.api.common import base
from app.api.v1 import didtx
from app.errors import AppError

from mongoengine import connect

from app.middleware import AuthMiddleware
from app.model import Didtx
from app.service import DidPublish

LOG = log.get_logger()


class App(falcon.API):
    def __init__(self, *args, **kwargs):
        super(App, self).__init__(*args, **kwargs)
        LOG.info("API Server is starting")

        # Simple endpoint for base
        self.add_route("/", base.BaseResource())
        # Retrieves all the rows
        self.add_route("/v1/didtx", didtx.Collection())
        # Retrieves the row according to confirmation ID
        self.add_route("/v1/didtx/confirmation_id/{confirmation_id}", didtx.ItemFromConfirmationId())
        # Retreives all rows belonging to a particular DID
        self.add_route("/v1/didtx/did/{did}", didtx.ItemFromDid())
        # Retreives Recent 5 rows belonging to a particular DID
        self.add_route("/v1/didtx/recent/did/{did}", didtx.RecentItemsFromDid())
        # Creates a new row
        self.add_route("/v1/didtx/create", didtx.Create())
        self.add_error_handler(AppError, AppError.handle)


# Connect to mongodb
LOG.info("Connecting to mongodb...")
connect(
    config.MONGO['DATABASE'],
    host="mongodb://" + config.MONGO['USERNAME'] + ":" + config.MONGO['PASSWORD'] + "@" +
         config.MONGO['HOST'] + ":" + str(config.MONGO['PORT']) + "/?authSource=admin"
)

# Set up CORS
cors = CORS(
    allow_all_origins=True,
    allow_all_headers=True,
    allow_all_methods=True)
# Initialize the application
LOG.info("Initializing the Falcon REST API service...")
application = App(middleware=[
    cors.middleware,
    AuthMiddleware(),
])

def verify_did_sidechain_endpoint():
    result = False
    response = requests.get
    return result

def send_tx_to_did_sidechain():
    did_publish = DidPublish()
    
    # Verify the DID sidechain is reachable
    response = did_publish.verify_node_availability()
    if(not (response and response["result"])):
        LOG.info("DID sidechain is currently not reachable...")
        return

    pending_transactions = []
    try:
        # Create raw transactions
        rows_pending = Didtx.objects(status=config.SERVICE_STATUS_PENDING)
        for row in rows_pending:
            tx = did_publish.create_raw_transaction(row.did, row.didRequest)
            tx_decoded = binascii.hexlify(tx).decode(encoding="utf-8")
            pending_transactions.append(tx_decoded)

        if pending_transactions:
            LOG.info("Found Pending transactions. Sending " + str(len(pending_transactions)) + "transactions to DID "
                                                                                          "sidechain now...")
            # Send transaction to DID sidechain
            response = did_publish.send_raw_transaction(pending_transactions)
            tx_id = response["result"]
            for row in rows_pending:
                # If for whatever reason, the transactions fail, put them in quarantine and come back to it later
                if tx_id:
                    row.status = config.SERVICE_STATUS_PROCESSING
                    row.blockchainTxId = tx_id
                else:
                    row.status = config.SERVICE_STATUS_QUARANTINE
                    row.extraInfo = response["error"]
                    LOG.info("Error sending transaction for id:" + str(row.id) + " did:" + row.did + " Error: " + str(row.extraInfo))
                row.save()

        # Get info about the recent transaction hash and save it to the database
        rows_processing = Didtx.objects(status=config.SERVICE_STATUS_PROCESSING)
        for row in rows_processing:
            blockchain_tx = did_publish.get_raw_transaction(row.blockchainTxId)
            if(blockchain_tx["result"]):
                confirmations = blockchain_tx["result"]["confirmations"]
                if confirmations >= 1:
                    row.status = config.SERVICE_STATUS_COMPLETED
                row.blockchainTx = blockchain_tx
            else:
                row.status = config.SERVICE_STATUS_QUARANTINE
                row.extraInfo = "Cannot find the transaction on the blockchain"
            row.save()

        # Try to process quarantined transactions one at a time
        rows_quarantined = Didtx.objects(status=config.SERVICE_STATUS_QUARANTINE)
        for row in rows_quarantined:
            did_publish.current_wallet_index += 1
            if did_publish.current_wallet_index > config.NUM_WALLETS - 1:
                did_publish.current_wallet_index = 1
            # Try sending each transaction one by one
            tx = did_publish.create_raw_transaction(row.did, row.didRequest)
            tx_decoded = binascii.hexlify(tx).decode(encoding="utf-8")
            response = did_publish.send_raw_transaction([tx_decoded])
            tx_id = response["result"]
            if tx_id:
                row.status = config.SERVICE_STATUS_PROCESSING
                row.blockchainTxId = tx_id
                row.extraInfo = ''
                break
            else:
                row.extraInfo = response["error"]
                LOG.info("Error sending transaction for id:" + str(row.id) + " did:" + row.did + " Error: " + str(row.extraInfo))
            row.save()

    except Exception as e:
        LOG.info("Could not send transactions to the DID sidechain:" + str(e))


# Start cron scheduler
scheduler = BackgroundScheduler()
scheduler.add_job(send_tx_to_did_sidechain, 'interval', seconds=config.CRON_INTERVAL)
scheduler.start()


