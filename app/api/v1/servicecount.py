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
    Handle for endpoint: /v1/service_count/{did}/{service}
    """

    def on_get(self, req, res, did, service):
        rows = Servicecount.objects(did=did, service=service)
        if rows:
            obj = [each.as_dict() for each in rows]
            self.on_success(res, obj)
        else:
            raise AppError()

