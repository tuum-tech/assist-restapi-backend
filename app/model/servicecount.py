import datetime

from mongoengine import IntField, StringField, DictField, DateTimeField, Document


class Servicecount(Document):
    did = StringField(max_length=128)
    service = StringField(max_length=32)
    count = IntField()
    created = DateTimeField()
    modified = DateTimeField(default=datetime.datetime.utcnow)

    def __repr__(self):
        return str(self.as_dict())

    def as_dict(self):
        return {
            "id": str(self.id),
            "did": self.did,
            "service": self.service,
            "count": self.count,
            "created": str(self.created),
            "modified": str(self.modified)
        }

    def save(self, *args, **kwargs):
        if not self.created:
            self.created = datetime.datetime.utcnow()
        self.modified = datetime.datetime.utcnow()
        return super(Servicecount, self).save(*args, **kwargs)