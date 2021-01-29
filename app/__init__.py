# -*- coding: utf-8 -*-
import falcon

from app import log, config

from apscheduler.schedulers.background import BackgroundScheduler

from app.api.common import base
from app.api.v1 import didtx, did_document, servicecount
from app.errors import AppError

from mongoengine import connect

from app.middleware import AuthMiddleware
from app.model import Didtx, DidDocument, Didstate

from app.cronjob import cron_send_tx_to_did_sidechain, cron_update_recent_did_documents, cron_send_daily_stats

LOG = log.get_logger()


class App(falcon.API):
    def __init__(self, *args, **kwargs):
        super(App, self).__init__(*args, **kwargs)
        LOG.info("API Server is starting")

        # Simple endpoint for base
        self.add_route("/", base.BaseResource())
        # Retrieves all the rows

        # Retrieves the row according to confirmation ID
        self.add_route("/v1/didtx/confirmation_id/{confirmation_id}", didtx.ItemFromConfirmationId())
        # Retreives all rows belonging to a particular DID
        self.add_route("/v1/didtx/did/{did}", didtx.ItemFromDid())
        # Retreives recent 5 rows belonging to a particular DID
        self.add_route("/v1/didtx/recent/did/{did}", didtx.RecentItemsFromDid())
        # Creates a new row 
        self.add_route("/v1/didtx/create", didtx.Create())

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
if not config.PRODUCTION:
    scheduler = BackgroundScheduler()
    scheduler.add_job(cron_send_tx_to_did_sidechain, 'interval', seconds=config.CRON_INTERVAL)
    scheduler.add_job(cron_update_recent_did_documents, 'interval', seconds=config.CRON_INTERVAL)
    scheduler.add_job(cron_send_daily_stats, 'interval', hours=24)
    scheduler.start()
