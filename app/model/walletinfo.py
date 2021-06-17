import datetime

from mongoengine import StringField, IntField, DateTimeField, Document


class WalletInfo(Document):
    address = StringField(max_length=128)
    nonce = IntField()
    created = DateTimeField()
    modified = DateTimeField(default=datetime.datetime.utcnow)

    def __repr__(self):
        return str(self.as_dict())

    def as_dict(self):
        return {
            "address": str(self.address),
            "nonce": self.nonce,
            "created": str(self.created),
            "modified": str(self.modified)
        }

    def save(self, *args, **kwargs):
        if not self.created:
            self.created = datetime.datetime.utcnow()
        self.modified = datetime.datetime.utcnow()
        return super(WalletInfo, self).save(*args, **kwargs)
