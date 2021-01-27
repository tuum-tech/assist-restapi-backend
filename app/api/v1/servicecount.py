# -*- coding: utf-8 -*-

from ratelimit import limits, RateLimitException
from backoff import on_exception, expo

from app import log
from app.api.common import BaseResource
from app.model import Servicecount
from app.service import get_service_count, api_rate_limit_reached
from app.config import RATE_LIMIT_PERIOD, RATE_LIMIT_CALLS

LOG = log.get_logger()


class GetServiceCountSpecificDidAndService(BaseResource):
    """
    Handle for endpoint: /v1/service_count/{service}/{did}
    """

    @on_exception(expo, RateLimitException, on_backoff=api_rate_limit_reached, max_tries=2)
    @limits(calls=RATE_LIMIT_CALLS, period=RATE_LIMIT_PERIOD)
    def on_get(self, req, res, service, did):
        LOG.info(f'Enter /v1/service_count/{service}/{did}')
        rows = Servicecount.objects(did=did.replace("did:elastos:", "").split("#")[0])
        if rows:
            obj = rows[0].service_count_as_dict(service)
        else:
            obj = {
                "id": "",
                "did": did,
                "service": service,
                "count": 0,
                "total_count": 0,
                "created": "never",
                "modified": "never"
            }
        self.on_success(res, obj)


class GetServiceCountAllServices(BaseResource):
    """
    Handle for endpoint: /v1/service_count/statistics
    """

    @on_exception(expo, RateLimitException, on_backoff=api_rate_limit_reached, max_tries=2)
    @limits(calls=RATE_LIMIT_CALLS, period=RATE_LIMIT_PERIOD)
    def on_get(self, req, res):
        LOG.info(f'Enter /v1/service_count/statistics')
        result = get_service_count()
        self.on_success(res, result)
