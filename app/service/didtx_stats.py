# -*- coding: utf-8 -*-
from datetime import datetime, timedelta
from pymongo import MongoClient

from app import config


def get_didtx_count():
    mongo_client = MongoClient(config.MONGO_CONNECT_HOST)
    db = mongo_client.assistdb

    result = {
        "today": {},
        "total": {}
    }

    date_today = datetime.utcnow() - timedelta(hours=24)
    result_today = db.didtx.aggregate([
        {"$match": {"created": {"$gt": date_today}}},
        {"$group": {"_id": "$requestFrom", "count": {"$sum": 1}}},
        {"$project": {"_id": 0, "name": "$_id", "count": "$count"}}
    ])
    for r in result_today:
        result["today"][r["name"]] = r["count"]

    result_total = db.didtx.aggregate([
        {"$group": {"_id": "$requestFrom", "count": {"$sum": 1}}},
        {"$project": {"_id": 0, "name": "$_id", "count": "$count"}}
    ])

    for r in result_total:
        result["total"][r["name"]] = r["count"]

    return result
