# -*- coding: utf-8 -*-
import datetime

from app.model import Didtx


def get_didtx_count():
    rows = Didtx.objects()

    result = {
        "today": {},
        "total": {}
    }
    if rows:
        for row in rows:
            if row.requestFrom in result["total"].keys():
                result["total"][row.requestFrom] += 1
            else:
                result["total"][row.requestFrom] = 1
            time_since_created = datetime.datetime.utcnow() - row.created

            if (time_since_created.total_seconds() / (60.0 * 60.0)) < 24:
                if row.requestFrom in result["today"].keys():
                    result["today"][row.requestFrom] += 1
                else:
                    result["today"][row.requestFrom] = 1
    return result
