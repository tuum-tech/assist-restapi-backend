# -*- coding: utf-8 -*-

import re
import falcon

from app import log
from app.api.common import BaseResource
from app.model import Didtx
from app.errors import (
    AppError,
    InvalidParameterError,
)

LOG = log.get_logger()


class Collection(BaseResource):
    """
    Handle for endpoint: /v1/didtx
    """

    def on_get(self, req, res):
        rows = []
        for i in Didtx.objects:
            row = {
                'id': i.id,
                'didRequest': i.didRequest,
                'created': i.created,
                'status': i.status
            }
            rows.append(row)
        self.on_success(res, rows)


class Item(BaseResource):
    """
    Handle for endpoint: /v1/didtx/{id}
    """

    def on_get(self, req, res, request_id):
        request_obj = Didtx.objects(id=request_id)
        self.on_success(res, request_obj)


class Create(BaseResource):
    """
    Handle for endpoint: /v1/didtx/create
    """

    def on_get(self, req, res, request_id):
        request_obj = Didtx.objects(id=request_id)
        self.on_success(res, request_obj)


class Send(BaseResource):
    """
    Handle for endpoint: /v1/didtx/send
    """

    def on_get(self, req, res, request_id):
        request_obj = Didtx.objects(id=request_id)
        self.on_success(res, request_obj)
