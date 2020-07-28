# -*- coding: utf-8 -*-

from app import log
from app.api.common import BaseResource
from app.model import Servicecount

LOG = log.get_logger()


class GetServiceCountSpecificDidAndService(BaseResource):
    """
    Handle for endpoint: /v1/service_count/{service}/{did}
    """

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

    def on_get(self, req, res):
        LOG.info(f'Enter /v1/service_count/statistics')
        rows = Servicecount.objects()

        # Add a new service to this array in the future
        services = ["did_publish"]

        obj = {}
        for service in services:
            obj[service] = {
                "users": 0,
                "today": 0,
                "total": 0
            }

        if rows:
            for item in rows:
                row = item.as_dict()
                for service in services:
                    if service in row["data"].keys():
                        obj[service]["users"] += 1
                        obj[service]["today"] += row["data"][service]["count"]
                        obj[service]["total"] += row["data"][service]["total_count"]

        self.on_success(res, obj)
