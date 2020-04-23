import falcon
import requests
import json
from .dbRepository import DbRepository

class CreateTransaction:
    def on_get(self, req, resp):
        """Handles Get requests"""
        service = DbRepository()
        didId = req.get_param('didid', True)
        signedPayload = req.get_param('payload', True)
        response = service.createTransaction(didId, signedPayload)
        resp.media = response