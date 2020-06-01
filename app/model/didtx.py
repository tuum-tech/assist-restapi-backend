import datetime

from mongoengine import StringField, DictField, DateTimeField, Document


class Didtx(Document):
    didId = StringField(max_length=120)
    didRequest = DictField()
    status = StringField(max_length=32)
    blockchainTx = DictField()
    created = DateTimeField()
    modified = DateTimeField(default=datetime.datetime.now)

    def __repr__(self):
        return "<Didtx(id='%s', didRequest='%s', created='%s', status='%s')>" % (
            self.id,
            self.didRequest,
            self.created,
            self.status,
        )
