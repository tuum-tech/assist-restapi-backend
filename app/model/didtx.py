import datetime

from mongoengine import StringField, DictField, DateTimeField, Document


class Didtx(Document):
    did = StringField(max_length=128)
    requestFrom = StringField(max_length=128)
    didRequestDid = StringField(max_length=128)
    didRequest = DictField()
    status = StringField(max_length=32)
    memo = StringField()
    extraInfo = DictField()
    blockchainTxId = StringField(max_length=128)
    blockchainTx = DictField()
    version = StringField()
    created = DateTimeField()
    modified = DateTimeField(default=datetime.datetime.utcnow)

    def __repr__(self):
        return str(self.as_dict())

    def as_dict(self):
        return {
            "id": str(self.id),
            "did": self.did,
            "requestFrom": self.requestFrom,
            "didRequestDid": self.didRequestDid,
            "didRequest": self.didRequest,
            "status": self.status,
            "memo": self.memo,
            "extraInfo": self.extraInfo,
            "blockchainTxId": self.blockchainTxId,
            "blockchainTx": self.blockchainTx,
            "version": self.version if self.version else "1",
            "created": str(self.created),
            "modified": str(self.modified)
        }

    def save(self, *args, **kwargs):
        if not self.created:
            self.created = datetime.datetime.utcnow()
        self.modified = datetime.datetime.utcnow()
        return super(Didtx, self).save(*args, **kwargs)
