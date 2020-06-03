# -*- coding: utf-8 -*-

from app import log
from app.api.common import BaseResource
from app.model import Didtx
from app.errors import (
    AppError,
)

LOG = log.get_logger()


class Collection(BaseResource):
    """
    Handle for endpoint: /v1/didtx
    """

    def on_get(self, req, res):
        rows = Didtx.objects()
        if rows:
            obj = [each.as_dict() for each in rows]
            self.on_success(res, obj)
        else:
            raise AppError()


class ItemFromConfirmationId(BaseResource):
    """
    Handle for endpoint: /v1/didtx/id/{confirmation_id}
    """

    def on_get(self, req, res, confirmation_id):
        rows = Didtx.objects(id=confirmation_id)
        if rows:
            row = [each.as_dict() for each in rows][0]
            self.on_success(res, row)
        else:
            raise AppError()


class ItemFromDid(BaseResource):
    """
    Handle for endpoint: /v1/didtx/did/{did}
    """

    def on_get(self, req, res, did):
        rows = Didtx.objects(did=did)
        if rows:
            obj = [each.as_dict() for each in rows]
            self.on_success(res, obj)
        else:
            raise AppError()


class Create(BaseResource):
    """
    Handle for endpoint: /v1/didtx/create
    """

    def on_post(self, req, res):
        data = req.media
        did_request = data["didRequest"]
        did = did_request["proof"]["verificationMethod"].replace("did:elastos:", "").split("#")[0]

        # TODO: Verify whether the did_request is valid/authenticated

        row = Didtx(
            did=did,
            requestFrom=data["didId"],
            didRequest=did_request,
            status="Pending"
        )
        row.save()
        result = {
            "confirmation_id": str(row.id)
        }
        self.on_success(res, result)
