# -*- coding: utf-8 -*-
import base64
import json

from ratelimit import limits, RateLimitException
from backoff import on_exception, expo

from app import log, config
from app.api.common import BaseResource
from app.config import RATE_LIMIT_CREATE_DID, RATE_LIMIT_PERIOD, RATE_LIMIT_CALLS
from app.model import Didtx
from app.model import Servicecount
from app.service import DidPublish, DidSidechainRpc, api_rate_limit_reached
from app.errors import (
    InvalidParameterError, NotFoundError, UserNotExistsError, DailyLimitReachedError
)

LOG = log.get_logger()


class Create(BaseResource):
    """
    Handle for endpoint: /v1/didtx/create
    """

    @on_exception(expo, RateLimitException, on_backoff=api_rate_limit_reached, max_tries=2)
    @limits(calls=RATE_LIMIT_CREATE_DID, period=RATE_LIMIT_PERIOD)
    def on_post(self, req, res):
        LOG.info(f'Enter /v1/didtx/create')
        data = req.media
        did_request = data["didRequest"]
        memo = data["memo"]

        did_request_payload = did_request["payload"]
        did_request_payload = did_request_payload + "=" * divmod(len(did_request_payload), 4)[1]
        did_request_payload = json.loads(base64.urlsafe_b64decode(did_request_payload))
        did_request_did = did_request_payload["id"].replace("did:elastos:", "").split("#")[0]

        try:
            caller_did = data["did"].replace("did:elastos:", "").split("#")[0]
            # Verify whether the DID who's making the call, is valid
            did_sidechain_rpc = DidSidechainRpc()
            did_resolver_result = did_sidechain_rpc.resolve_did(caller_did)
            if not did_resolver_result:
                err_message = f"Invalid DID: {caller_did}"
                LOG.info(f"Error /v1/didtx/create: {err_message}")
                raise UserNotExistsError(description=err_message)
        except:
            LOG.info(f"Info /v1/didtx/create: Defaulting to DID found inside didRequest payload")
            caller_did = did_request_did

        # First verify whether this is a valid payload
        did_publish = DidPublish()
        tx = did_publish.create_raw_transaction(did_request_did, did_request)
        if not tx:
            err_message = "Could not generate a valid transaction out of the given didRequest"
            LOG.info(f"Error /v1/didtx/create: {err_message}")
            raise InvalidParameterError(description=err_message)

        # Check the number of times this did has used the "did_publish" service
        count = self.retrieve_service_count(caller_did, config.SERVICE_DIDPUBLISH)
        count_did_request_did = self.retrieve_service_count(did_request_did, config.SERVICE_DIDPUBLISH)
        if count_did_request_did > count:
            count = count_did_request_did

        result = {}
        # Check if the row already exists with the same didRequest
        transaction_sent = self.transaction_already_sent(caller_did, did_request, memo)
        if transaction_sent:
            result["duplicate"] = True
            result["service_count"] = count
            result["confirmation_id"] = str(transaction_sent.id)
        else:
            result["service_count"] = self.retrieve_service_count(caller_did, config.SERVICE_DIDPUBLISH)
            result["duplicate"] = False
            # If less than limit, increment and allow, otherwise, not allowed as max limit is reached
            if count < config.SERVICE_DIDPUBLISH_DAILY_LIMIT:
                row = Didtx(
                    did=caller_did,
                    requestFrom=data["requestFrom"],
                    didRequestDid=did_request_did,
                    didRequest=did_request,
                    memo=memo,
                    version="1",
                    status="Pending"
                )
                row.save()
                self.add_service_count_record(caller_did, config.SERVICE_DIDPUBLISH)
                self.add_service_count_record(did_request_did, config.SERVICE_DIDPUBLISH)
                result["confirmation_id"] = str(row.id)
            else:
                LOG.info(f"Error /v1/didtx/create: Daily limit reached for this DID")
                raise DailyLimitReachedError()
        self.on_success(res, result)

    def transaction_already_sent(self, did, did_request, memo):
        rows = Didtx.objects(did=did, status="Processing")
        if rows:
            return rows[0]
        rows = Didtx.objects(did=did, status="Pending")
        if rows:
            row = rows[0]
            row.memo = memo
            row.didRequest = did_request
            row.save()
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


class ItemFromConfirmationId(BaseResource):
    """
    Handle for endpoint: /v1/didtx/confirmation_id/{confirmation_id}
    """

    @on_exception(expo, RateLimitException, on_backoff=api_rate_limit_reached, max_tries=2)
    @limits(calls=RATE_LIMIT_CALLS, period=RATE_LIMIT_PERIOD)
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

    @on_exception(expo, RateLimitException, on_backoff=api_rate_limit_reached, max_tries=2)
    @limits(calls=RATE_LIMIT_CALLS, period=RATE_LIMIT_PERIOD)
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

    @on_exception(expo, RateLimitException, on_backoff=api_rate_limit_reached, max_tries=2)
    @limits(calls=RATE_LIMIT_CALLS, period=RATE_LIMIT_PERIOD)
    def on_get(self, req, res, did):
        LOG.info(f'Enter /v1/didtx/recent/did/{did}')
        rows = Didtx.objects(did=did.replace("did:elastos:", "").split("#")[0]).order_by('-modified')[:5]
        if rows:
            obj = [each.as_dict() for each in rows]
            self.on_success(res, obj)
        else:
            LOG.info(f"Error /v1/didtx/recent/did/{did}")
            raise NotFoundError()

