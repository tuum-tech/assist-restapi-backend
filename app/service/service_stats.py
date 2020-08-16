# -*- coding: utf-8 -*-

from app.model import Servicecount


def get_service_count():
    rows = Servicecount.objects()

    # Add a new service to this array in the future
    services = ["did_publish"]

    result = {}
    for service in services:
        result[service] = {
            "users": 0,
            "today": 0,
            "total": 0
        }

    if rows:
        for item in rows:
            row = item.as_dict()
            for service in services:
                if service in row["data"].keys():
                    result[service]["users"] += 1
                    result[service]["today"] += row["data"][service]["count"]
                    result[service]["total"] += row["data"][service]["total_count"]
    return result
