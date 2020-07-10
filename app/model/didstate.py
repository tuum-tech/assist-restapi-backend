import datetime

from mongoengine import IntField, DateTimeField, Document


class Didstate(Document):
    currentHeight = IntField()
    created = DateTimeField()
    modified = DateTimeField(default=datetime.datetime.utcnow)

    def __repr__(self):
        return str(self.as_dict())

    def as_dict(self):
        return {
            "id": str(self.id),
            "currentHeight": self.currentHeight,
            "created": str(self.created),
            "modified": str(self.modified)
        }

    def save(self, *args, **kwargs):
        if not self.created:
            self.created = datetime.datetime.utcnow()
        self.modified = datetime.datetime.utcnow()
        return super(Didstate, self).save(*args, **kwargs)
