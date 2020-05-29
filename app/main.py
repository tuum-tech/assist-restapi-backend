# -*- coding: utf-8 -*-

import falcon

from falcon_cors import CORS

from app import log
from app.database import init_session

from app.api.common import base
#from app.api.v1 import didtx
from app.errors import AppError

LOG = log.get_logger()


class App(falcon.API):
    def __init__(self, *args, **kwargs):
        super(App, self).__init__(*args, **kwargs)
        LOG.info("API Server is starting")

        self.add_route("/", base.BaseResource())
        #self.add_route("/v1/didtx", didtx.Collection())
        #self.add_route("/v1/didtx/{request_id}", didtx.Item())
        #self.add_route("/v1/didtx/create", didtx.Create())
        #self.add_route("/v1/didtx/send", didtx.Send())

        self.add_error_handler(AppError, AppError.handle)

init_session()
middleware = CORS(
    allow_all_origins=True,
    allow_all_headers=True,
    allow_all_methods=True)
application = App(middleware=[cors.middleware])


if __name__ == "__main__":
    from wsgiref import simple_server

    httpd = simple_server.make_server("0.0.0.0", 8000, application)
    httpd.serve_forever()