import falcon
import requests
import json
from .mongoDatabase import MongoDatabase

class VerifyTransaction:
    def on_get(self, req, resp):
        """Handles get requests"""
        transactionId = req.get_param('transactionid', True)
        database = MongoDatabase()
        response = database.get_transaction(transactionId)
        resp.media = response