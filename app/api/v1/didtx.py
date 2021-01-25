# -*- coding: utf-8 -*-
from ratelimit import limits

from app import log, config
from app.api.common import BaseResource
from app.config import RATE_LIMIT_CALLS, RATE_LIMIT_PERIOD
from app.model import Didtx
from app.model import Servicecount
from app.service import DidPublish
from app.errors import (
    InvalidParameterError, NotFoundError
)

LOG = log.get_logger()


class Collection(BaseResource):
    """
    Handle for endpoint: /v1/didtx
    """

    def on_get(self, req, res):
        LOG.info(f'Enter /v1/didtx')
        rows = Didtx.objects()
        if rows:
            obj = [each.as_dict() for each in rows]
            self.on_success(res, obj)
        else:
            LOG.info(f"Error /v1/didtx")
            raise NotFoundError()


class ItemFromConfirmationId(BaseResource):
    """
    Handle for endpoint: /v1/didtx/confirmation_id/{confirmation_id}
    """

    def on_get(self, req, res, confirmation_id):
        LOG.info(f'Enter /v1/didtx/confirmation_id/{confirmation_id}')
        try:
            rows = Didtx.objects(id=confirmation_id)
            if rows:
                row = [each.as_dict() for each in rows][0]
                self.on_success(res, row)
            else:
                LOG.info(f"Error /v1/didtx/id/{confirmation_id}")
                raise NotFoundError()
        except Exception as e:
            LOG.info(f"Error /v1/didtx/id/{confirmation_id}: {str(e)}")
            raise NotFoundError()


class ItemFromDid(BaseResource):
    """
    Handle for endpoint: /v1/didtx/did/{did}
    """

    def on_get(self, req, res, did):
        LOG.info(f'Enter /v1/didtx/did/{did}')
        rows = Didtx.objects(did=did.replace("did:elastos:", "").split("#")[0]).order_by('-modified')
        if rows:
            obj = [each.as_dict() for each in rows]
            self.on_success(res, obj)
        else:
            LOG.info(f"Error /v1/didtx/did/{did}")
            raise NotFoundError()


class RecentItemsFromDid(BaseResource):
    """
    Handle for endpoint: /v1/didtx/recent/did/{did}
    """

    def on_get(self, req, res, did):
        LOG.info(f'Enter /v1/didtx/recent/did/{did}')
        rows = Didtx.objects(did=did.replace("did:elastos:", "").split("#")[0]).order_by('-modified')[:5]
        if rows:
            obj = [each.as_dict() for each in rows]
            self.on_success(res, obj)
        else:
            LOG.info(f"Error /v1/didtx/recent/did/{did}")
            raise NotFoundError()


class Create(BaseResource):
    """
    Handle for endpoint: /v1/didtx/create
    """

    @limits(calls=RATE_LIMIT_CALLS, period=RATE_LIMIT_PERIOD)
    def on_post(self, req, res):
        LOG.info(f'Enter /v1/didtx/create')
        data = req.media
        did_request = data["didRequest"]
        memo = data["memo"]
        did = data["did"].replace("did:elastos:", "").split("#")[0]

        # TODO: Verify whether the did is valid

        # TODO: Verify whether the did_request is valid

        did_to_consume = did_request["proof"]["verificationMethod"].replace("did:elastos:", "").split("#")[0]

        # First verify whether this is a valid payload
        did_publish = DidPublish()
        tx = did_publish.create_raw_transaction(did, did_request)
        if not tx:
            LOG.info(f"Error /v1/didtx/create")
            raise InvalidParameterError(
                description="Could not generate a valid transaction out of the given didRequest")

        # Check the number of times this did has used the "did_publish" service
        count = self.retrieve_service_count(did, config.SERVICE_DIDPUBLISH)
        count_did_to_consume = self.retrieve_service_count(did_to_consume, config.SERVICE_DIDPUBLISH)
        if count_did_to_consume > count:
            count = count_did_to_consume

        result = {}
        # Check if the row already exists with the same didRequest
        transaction_sent = self.transaction_already_sent(did, did_request, memo)
        if transaction_sent:
            result["duplicate"] = True
            result["service_count"] = count
            result["confirmation_id"] = str(transaction_sent.id)
        else:
            # If less than limit, increment and allow, otherwise, not allowed as max limit is reached
            if count < config.SERVICE_DIDPUBLISH_DAILY_LIMIT:
                row = Didtx(
                    did=did,
                    requestFrom=data["requestFrom"],
                    didRequest=did_request,
                    memo=memo,
                    status="Pending"
                )
                row.save()
                self.add_service_count_record(did, config.SERVICE_DIDPUBLISH)
                self.add_service_count_record(did_to_consume, config.SERVICE_DIDPUBLISH)
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
                if row.status == "Pending":
                    # Check if header is the same(whether create or update operation)
                    if row.didRequest["header"] == did_request["header"]:
                        # Check if payload is the same(the info to be published)
                        if row.didRequest["payload"] == did_request["payload"]:
                            # Check if memo is the same. If not, just update the row with the new memo passed
                            if row.memo != memo:
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
                elif row.status == "Processing":
                    return row
        return None

    def retrieve_service_count(self, did, service):
        count = 0
        rows = Servicecount.objects(did=did)
        if rows:
            row = rows[0].service_count_as_dict(service)
            count = row["count"]
        return count

    def add_service_count_record(self, did, service):
        rows = Servicecount.objects(did=did)
        service_default_count = {
            "count": 1,
            "total_count": 1
        }
        if rows:
            row = rows[0]
            if service in row.data.keys():
                if "count" not in row.data[service].keys():
                    row.data[service] = service_default_count
                else:
                    row.data[service]["count"] += 1
                    row.data[service]["total_count"] += 1
            else:
                row.data[service] = service_default_count
        else:
            row = Servicecount(
                did=did,
                data={service: service_default_count}
            )
        row.save()
