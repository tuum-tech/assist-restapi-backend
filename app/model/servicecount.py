import datetime

from mongoengine import StringField, DictField, DateTimeField, Document


class Servicecount(Document):
    did = StringField(max_length=128)
    service = StringField(max_length=32)
    created = DateTimeField()

    def __repr__(self):
        return str(self.as_dict())

    def as_dict(self):
        return {
            "id": str(self.id),
            "did": self.did,
            "service": self.service,
            "created": str(self.created),
            "modified": str(self.modified)
        }

    def save(self, *args, **kwargs):
        if not self.created:
            self.created = datetime.datetime.now()
        self.modified = datetime.datetime.now()
        return super(Servicecount, self).save(*args, **kwargs)