import falcon
import requests
import json
from .dbRepository import DbRepository

class VerifyTransaction:
    def on_get(self, req, resp):
        """Handles get requests"""
        service = DbRepository()
        transactionId = req.get_param('transactionid', True)
        response = service.verifyTransaction(transactionId)
        resp.media = response