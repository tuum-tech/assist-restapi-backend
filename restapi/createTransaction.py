import falcon
import requests
import json
from .mongoDatabase import MongoDatabase

class CreateTransaction:
    def on_post(self, req, resp):
       print("Creating new transaction")
       try:
        body = req.stream.read()
        doc = json.loads(body.decode('utf-8'))
        repository = MongoDatabase()
        transaction = repository.create_transaction(doc["didId"], doc["didRequest"])
        resp.media = transaction 
       except AttributeError:
            raise falcon.HTTPBadRequest(
                'Invalid post',
                'Payload must be submitted in the request body.')


       resp.status = falcon.HTTP_201
       resp.location = '/%s/create'

       

       