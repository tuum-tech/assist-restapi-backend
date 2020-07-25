import datetime

from mongoengine import StringField, IntField, DictField, DateTimeField, Document


class DidDocument(Document):
    did = StringField(max_length=128)
    documents = DictField()
    num_searches = IntField()
    created = DateTimeField()
    modified = DateTimeField(default=datetime.datetime.utcnow)

    def __repr__(self):
        return str(self.as_dict())

    def as_dict(self):
        return {
            "id": str(self.id),
            "did": self.did,
            "documents": self.documents,
            "num_searches": self.num_searches,
            "created": str(self.created),
            "modified": str(self.modified)
        }

    def save(self, *args, **kwargs):
        if not self.created:
            self.created = datetime.datetime.utcnow()
        self.modified = datetime.datetime.utcnow()
        return super(DidDocument, self).save(*args, **kwargs)