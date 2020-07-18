# -*- coding: utf-8 -*-

from app import log
from app.api.common import BaseResource
from app.model import Servicecount
from app.errors import (
    AppError,
)

LOG = log.get_logger()


class GetServiceCount(BaseResource):
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

class GetServiceStatistics(BaseResource):
    """
    Handle for endpoint: /v1/service_count/statistics
    """

    def on_get(self, req, res):
        LOG.info(f'Enter /v1/service_count/statistics')
        rows = Servicecount.objects()

        obj = {
            "did_publish":{
                "users": 0,
                "today": 0,
                "total": 0
            }
        }

        if rows:
            for item in rows:
                row = item.as_dict()
                if  row["data"]["did_publish"]:
                    obj["did_publish"]["users"] += 1
                    obj["did_publish"]["today"] +=  row["data"]["did_publish"]["count"]
                    obj["did_publish"]["total"] +=  row["data"]["did_publish"]["total_count"]

        
        self.on_success(res, obj)

