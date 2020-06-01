# -*- coding: utf-8 -*-

import falcon

from falcon_cors import CORS

from app import log, config

from app.api.common import base
from app.api.v1 import didtx
from app.errors import AppError

from mongoengine import connect

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
        # Creates a new row
        self.add_route("/v1/didtx/create", didtx.Create())
        self.add_error_handler(AppError, AppError.handle)


connect(
    config.MONGO['DATABASE'],
    host="mongodb://" + config.MONGO['USERNAME'] + ":" + config.MONGO['PASSWORD'] + "@" +
         config.MONGO['HOST'] + ":" + str(config.MONGO['PORT']) + "/?authSource=admin"
)

cors = CORS(
    allow_all_origins=True,
    allow_all_headers=True,
    allow_all_methods=True)
application = App(middleware=[cors.middleware])

if __name__ == "__main__":
    from wsgiref import simple_server

    httpd = simple_server.make_server("0.0.0.0", 8000, application)
    httpd.serve_forever()
