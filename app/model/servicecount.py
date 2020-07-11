import datetime

from mongoengine import IntField, StringField, DictField, DateTimeField, Document


class Servicecount(Document):
    did = StringField(max_length=128)
    data = DictField()
    created = DateTimeField()
    modified = DateTimeField(default=datetime.datetime.utcnow)

    def __repr__(self):
        return str(self.as_dict())

    def as_dict(self):
        return {
            "id": str(self.id),
            "did": self.did,
            "data": self.data,
            "created": str(self.created),
            "modified": str(self.modified)
        }

    def service_count_as_dict(self, service):
        return {
            "id": str(self.id),
            "did": self.did,
            "service": service,
            "count": self.data[service] if service in self.data.keys() else 0,
            "created": str(self.created),
            "modified": str(self.modified)
        }

    def save(self, *args, **kwargs):
        if not self.created:
            self.created = datetime.datetime.utcnow()
        self.modified = datetime.datetime.utcnow()
        return super(Servicecount, self).save(*args, **kwargs)