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
                'requestId': i.requestId,
                'didRequest': i.didRequest,
                'createdIn': i.createdIn,
                'status': i.status
            }
            rows.append(row)
        self.on_success(res, rows)


class Item(BaseResource):
    """
    Handle for endpoint: /v1/didtx/{request_id}
    """

    def on_get(self, req, res, request_id):
        try:
            transactionId = req.get_param('transactionid', True)
            database = Mongo()
            response = database.get_transaction(transactionId)
            resp.media = response

            user_db = User.find_one(session, user_id)
            self.on_success(res, user_db.to_dict())
        except NoResultFound:
            raise UserNotExistsError("user id: %s" % user_id)

