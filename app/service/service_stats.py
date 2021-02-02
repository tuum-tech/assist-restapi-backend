# -*- coding: utf-8 -*-
from datetime import datetime, timedelta

from pymongo import MongoClient

from app import config


def get_service_count():
    mongo_client = MongoClient(config.MONGO_CONNECT_HOST)
    db = mongo_client.assistdb

    result = {
        "did_publish": {}
    }
    for service in result.keys():
        result[service] = {
            "users": 0,
            "today": 0,
            "total": 0
        }

    result_users = db.didtx.aggregate([
        {"$group": {"_id": "$did", "count": {"$sum": 1}}},
        {"$project": {"_id": 0, "name": "$_id", "count": "$count"}}
    ])
    count_users = 0
    for _ in result_users:
        count_users += 1
    result["did_publish"]["users"] = count_users

    date_today = datetime.utcnow() - timedelta(hours=24)
    result_today = db.didtx.count_documents({"modified": {"$gt": date_today}})
    result["did_publish"]["today"] = result_today

    result_total = db.didtx.count_documents({})
    result["did_publish"]["total"] = result_total

    return result
