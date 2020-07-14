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
        rows = Servicecount.objects(did=did)
        if rows:
            obj = rows[0].service_count_as_dict(service)
            self.on_success(res, obj)
        else:
            raise AppError()

