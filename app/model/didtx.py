import datetime
import pymongo as mongo

from mongoengine import *


class Didtx(Document):
    didId = StringField(max_length=120)
    didRequest = DictField()
    status = StringField(max_length=32)
    blockchainTx = DictField()
    created = mongo.DateTimeField()
    modified = mongo.DateTimeField(default=datetime.datetime.now)

    def __repr__(self):
        return "<Didtx(id='%s', didRequest='%s', created='%s', status='%s')>" % (
            self.id,
            self.didRequest,
            self.created,
            self.status,
        )
