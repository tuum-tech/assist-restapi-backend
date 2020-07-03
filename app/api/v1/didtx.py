# -*- coding: utf-8 -*-

from app import log, config
from app.api.common import BaseResource
from app.model import Didtx
from app.model import Servicecount
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
        try:
            rows = Didtx.objects(id=confirmation_id)
            if rows:
                row = [each.as_dict() for each in rows][0]
                self.on_success(res, row)
            else:
                self.on_error(res, {
                    "status": "404",
                    "code": "404",
                    "message": "Not Found"
                })
        except:
            self.on_error(res, {
                    "status": "404",
                    "code": "404",
                    "message": "Not Found"
                })
        
        


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

class RecentItemsFromDid(BaseResource):
    """
    Handle for endpoint: /v1/didtx/recent/did/{did}
    """

    def on_get(self, req, res, did):
        rows = Didtx.objects(did=did.replace("did:elastos:", "").split("#")[0]).order_by('-modified')[:5]
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

        # Check the number of times this did has used the "did_publish" service
        count = self.retrieve_service_count(did, config.SERVICE_DIDPUBLISH)

        result = {}
        # Check if the row already exists with the same didRequest
        transactionSent = self.transaction_already_sent(did, did_request, memo)
        if transactionSent:
            result["duplicate"] = True
            result["service_count"] = count
            result["confirmation_id"] = str(transactionSent.id)
        else: 
            # If less than 10, increment and allow, otherwise, not allowed as max limit is reached
            if count < 10:
                row = Didtx(
                    did=did,
                    requestFrom=data["requestFrom"],
                    didRequest=did_request,
                    memo=memo,
                    status="Pending"
                )
                row.save()            
                self.add_service_count_record(did, config.SERVICE_DIDPUBLISH)
                result["confirmation_id"] = str(row.id)
            else:
                result["confirmation_id"] = ""
            result["service_count"] = self.retrieve_service_count(did, config.SERVICE_DIDPUBLISH) 
            result["duplicate"] = False
        self.on_success(res, result)

    def transaction_already_sent(self, did, did_request, memo):
        rows = Didtx.objects(did=did)
        if rows:
            for row in rows:
                # Only check transactions that are in Pending state
                if(row.status == "Pending"):
                    # Check if header is the same(whether create or update operation)
                    if(row.didRequest["header"] == did_request["header"]):
                        # Check if payload is the same(the info to be published)
                        if(row.didRequest["payload"] == did_request["payload"]):
                            # Check if memo is the same. If not, just update the row with the new memo passed
                            if(row.memo != memo):  
                                row.memo = memo   
                                row.save()                        
                        else:
                            # If payload is not the same, update the row with new didRequest 
                            row.didRequest = did_request                       
                            row.save()     
                    else:
                        # If header is not the same, update the row with new didRequest
                        row.didRequest = did_request
                        row.save()
                    return row
                # If another transaction for this DID is already Processing, return it because we 
                # don't want to create a new request without that first being processed successfully
                elif(row.status == "Processing"):
                    return row
        return None    

    def retrieve_service_count(self, did, service):
        count = 0
        rows = Servicecount.objects(did=did, service=service)
        if rows:
            row = rows[0]
            count = row.count
        return count

    def add_service_count_record(self, did, service):
        rows = Servicecount.objects(did=did, service=service)
        if rows:
            row = rows[0]
            row.count += 1
        else:
            row = Servicecount(
                did=did,
                service=service,
                count=1,
            ) 
        row.save()
