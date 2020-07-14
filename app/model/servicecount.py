import datetime

from mongoengine import StringField, DictField, DateTimeField, Document


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
        if not isinstance(self.data[service], dict):
            count = self.data[service]
            self.data[service] = {
                "count": count,
                "total_count": count
            }
            self.save()
        return {
            "id": str(self.id),
            "did": self.did,
            "service": service,
            "count": self.data[service]["count"] if service in self.data.keys() else 0,
            "total_count": self.data[service]["total_count"] if service in self.data.keys() else 0,
            "created": str(self.created),
            "modified": str(self.modified)
        }

    def save(self, *args, **kwargs):
        if not self.created:
            self.created = datetime.datetime.utcnow()
        self.modified = datetime.datetime.utcnow()
        return super(Servicecount, self).save(*args, **kwargs)