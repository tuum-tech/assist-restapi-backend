# -*- coding: utf-8 -*-
import time
from datetime import datetime

import falcon

from app import log, config

from apscheduler.schedulers.background import BackgroundScheduler

from app.api.common import base
from app.api.v1 import didtx, did_document, servicecount
from app.api.v2 import didtxv2
from app.errors import AppError

from mongoengine import connect

from app.middleware import AuthMiddleware
from app.model import Didtx, DidDocument, Didstate

from app.cronjob import cron_send_tx_to_did_sidechain
from app.cronjobv2 import cron_send_daily_stats_v2, cron_send_tx_to_did_sidechain_v2, cron_update_recent_did_documents

LOG = log.get_logger()


class App(falcon.API):
    def __init__(self, *args, **kwargs):
        super(App, self).__init__(*args, **kwargs)
        LOG.info("API Server is starting")

        # Simple endpoint for base
        self.add_route("/", base.BaseResource())

        # Creates a new row
        self.add_route("/v1/didtx/create", didtx.Create())
        # Creates a new row V2
        self.add_route("/v2/didtx/create", didtxv2.Create())

        # Retrieves the row according to confirmation ID
        self.add_route("/v1/didtx/confirmation_id/{confirmation_id}", didtx.ItemFromConfirmationId())
        # Retrieves the row according to confirmation ID v2
        self.add_route("/v2/didtx/confirmation_id/{confirmation_id}", didtxv2.ItemFromConfirmationId())

        # Retreives all rows belonging to a particular DID
        self.add_route("/v1/didtx/did/{did}", didtx.ItemFromDid())
        # Retreives all rows belonging to a particular DID V2
        self.add_route("/v2/didtx/did/{did}", didtxv2.ItemFromDid())

        # Retreives recent 5 rows belonging to a particular DID
        self.add_route("/v1/didtx/recent/did/{did}", didtx.RecentItemsFromDid())
        # Retreives recent 5 rows belonging to a particular DID v2
        self.add_route("/v2/didtx/recent/did/{did}", didtxv2.RecentItemsFromDid())

        # Retrieves the last 5 DID documents published for a particular DID
        self.add_route("/v1/documents/did/{did}", did_document.GetDidDocumentsFromDid())
        # Retrieves the last 5 DID documents published for a particular DID from a cryptoname
        self.add_route("/v1/documents/crypto_name/{crypto_name}", did_document.GetDidDocumentsFromCryptoname())

        # Retrieves the service count for a particular DID
        self.add_route("/v1/service_count/{service}/{did}", servicecount.GetServiceCountSpecificDidAndService())
        # Retrieves service statistics
        self.add_route("/v1/service_count/statistics", servicecount.GetServiceCountAllServices())

        self.add_error_handler(AppError, AppError.handle)


# Connect to mongodb
LOG.info("Connecting to mongodb...")
connect(
    config.MONGO['DATABASE'],
    host=config.MONGO_CONNECT_HOST
)

LOG.info("Initializing the Falcon REST API service...")
application = App(middleware=[
    AuthMiddleware(),
])

# Start cron scheduler
scheduler = BackgroundScheduler()
scheduler.add_job(cron_send_tx_to_did_sidechain, 'interval', seconds=config.CRON_INTERVAL)

scheduler.add_job(cron_send_tx_to_did_sidechain_v2, 'interval', seconds=config.CRON_INTERVAL_V2)
scheduler.add_job(cron_update_recent_did_documents, 'interval', seconds=config.CRON_INTERVAL)
scheduler.add_job(cron_send_daily_stats_v2, 'cron', day='*', hour=0, minute=0)

scheduler.start()
