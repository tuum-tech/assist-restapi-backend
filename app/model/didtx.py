import datetime
import pymongo as mongo

from mongoengine import *


class Didtx(Document):
    requestId = IntField(required=True, primary_key=True)
    didId = StringField(max_length=120)
    didRequest = DictField()
    status = StringField(max_length=32)
    blockchainTx = DictField()
    created = mongo.DateTimeField()
    modified = mongo.DateTimeField(default=datetime.datetime.now)

    def __repr__(self):
        return "<Didtx(requestId='%s', didRequest='%s', createdIn='%s', status='%s')>" % (
            self.requestId,
            self.didRequest,
            self.createdIn,
            self.status,
        )