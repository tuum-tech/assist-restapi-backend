# -*- coding: utf-8 -*-

from app.model import Servicecount


def get_service_count():
    rows = Servicecount.objects()

    result = {
        "did_publish": {}
    }
    for service in result.keys():
        result[service] = {
            "users": 0,
            "today": 0,
            "total": 0
        }

    if rows:
        for item in rows:
            row = item.as_dict()
            for service in result.keys():
                if service in row["data"].keys():
                    result[service]["users"] += 1
                    result[service]["today"] += row["data"][service]["count"]
                    result[service]["total"] += row["data"][service]["total_count"]
    return result
