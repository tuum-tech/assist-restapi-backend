# -*- coding: utf-8 -*-

import falcon
import json

try:
    from collections import OrderedDict
except ImportError:
    OrderedDict = dict

from app import log
from app.config import BRAND_NAME, MONGO
from app.errors import NotFoundError

LOG = log.get_logger()


class BaseResource(object):
    HELLO_WORLD = {
        "server": "%s" % BRAND_NAME,
        "database": "mongo: (%s)" % (MONGO["HOST"]),
    }

    def to_json(self, body_dict):
        return json.dumps(body_dict)

    def on_error(self, res, error=None):
        res.status = error["status"]
        meta = OrderedDict()
        meta["code"] = error["code"]
        meta["message"] = error["message"]

        obj = OrderedDict()
        obj["meta"] = meta
        res.body = self.to_json(obj)

    def on_success(self, res, data=None):
        res.status = falcon.HTTP_200
        meta = OrderedDict()
        meta["code"] = 200
        meta["message"] = "OK"

        obj = OrderedDict()
        obj["meta"] = meta
        obj["data"] = data
        res.body = self.to_json(obj)

    def on_get(self, req, res):
        if req.path == "/":
            res.status = falcon.HTTP_200
            res.body = self.to_json(self.HELLO_WORLD)
        else:
            raise NotFoundError(method="GET", url=req.path)

    def on_post(self, req, res):
        raise NotFoundError(method="POST", url=req.path)

    def on_put(self, req, res):
        raise NotFoundError(method="PUT", url=req.path)

    def on_delete(self, req, res):
        raise NotFoundError(method="DELETE", url=req.path)