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
        rows = Didtx.objects(did=did.replace("did:elastos:", "").split("#")[0])
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
        memo = data["memo"]
        did = did_request["proof"]["verificationMethod"].replace("did:elastos:", "").split("#")[0]

        # TODO: Verify whether the did_request is valid/authenticated

        # Check if the row already exists with the same didRequest
        does_exist = False
        rows = Didtx.objects(did=did)
        if rows:
            row = rows[0]
            if(did_request["header"] == row.didRequest["header"] and did_request["payload"] == row.didRequest["payload"]):
                does_exist = True
        
        # If it doesn't exist in the database, create a new request
        if not does_exist:
            row = Didtx(
                did=did,
                requestFrom=data["requestFrom"],
                didRequest=did_request,
                memo=memo,
                status="Pending"
            )
            row.save()
        result= { 
            "confirmation_id": str(row.id)
        }
        self.on_success(res, result)

