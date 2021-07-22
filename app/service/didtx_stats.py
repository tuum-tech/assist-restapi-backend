# -*- coding: utf-8 -*-
from datetime import datetime, timedelta
from pymongo import MongoClient

from app import log, config
from app.service import send_slack_notification

LOG = log.get_logger()


def get_didtx_count():
    mongo_client = MongoClient(config.MONGO_CONNECT_HOST)
    db = mongo_client.get_database(config.MONGO["DATABASE"])

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
        app_name = r["name"].split("#", 1)[0]
        if app_name in result["total"].keys():
            result["today"][app_name] += r["count"]
        else:
            result["today"][app_name] = r["count"]

    result_total = db.didtx.aggregate([
        {"$group": {"_id": "$requestFrom", "count": {"$sum": 1}}},
        {"$project": {"_id": 0, "name": "$_id", "count": "$count"}}
    ])
    for r in result_total:
        app_name = r["name"].split("#", 1)[0]
        if app_name in result["total"].keys():
            result["total"][app_name] += r["count"]
        else:
            result["total"][app_name] = r["count"]

    return result


def api_rate_limit_reached(details):
    message1 = "Global rate limit reached"
    message2 = f"Max limit Allowed: {config.RATE_LIMIT_CREATE_DID} calls per {config.RATE_LIMIT_PERIOD / 60.0} minutes"
    message3 = "Backing off {wait:0.1f} seconds after {tries} tries " \
               "calling function {target} with args {args} and kwargs " \
               "{kwargs}".format(**details)
    LOG.info(f"Method: api_rate_limit_reached: {message1}\n{message2}\n{message3}")
    slack_blocks = [
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": message1
            }
        },
        {
            "type": "divider"
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": message2
            }
        },
        {
            "type": "divider"
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": message3
            }
        },
        {
            "type": "divider"
        }
    ]
    send_slack_notification(slack_blocks)
