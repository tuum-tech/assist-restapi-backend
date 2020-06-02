import datetime

from mongoengine import StringField, DictField, DateTimeField, Document


class Didtx(Document):
    did = StringField(max_length=128)
    requestFrom = StringField(max_length=128)
    didRequest = DictField()
    status = StringField(max_length=32)
    blockchainTxId = StringField(max_length=128)
    blockchainTx = DictField()
    created = DateTimeField()
    modified = DateTimeField(default=datetime.datetime.now)

    def __repr__(self):
        return str(self.as_dict())

    def as_dict(self):
        return {
            "id": str(self.id),
            "did": self.did,
            "requestFrom": self.requestFrom,
            "didRequest": self.didRequest,
            "status": self.status,
            "blockchainTx": self.blockchainTx,
            "created": str(self.created),
            "modified": str(self.modified)
        }

    def save(self, *args, **kwargs):
        if not self.created:
            self.created = datetime.datetime.now()
        self.modified = datetime.datetime.now()
        return super(Didtx, self).save(*args, **kwargs)
