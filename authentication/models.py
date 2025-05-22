# authentication/models.py

from datetime import datetime
from mongoengine import (
    Document,
    StringField,
    ReferenceField,
    BooleanField,
    DateTimeField,
)

class Address(Document):
    user = ReferenceField('User', required=True)
    street = StringField(required=True)
    city = StringField(required=True)
    state = StringField()  # Optional depending on country
    country = StringField(required=True)
    zip_code = StringField(required=True)

    is_default_shipping = BooleanField(default=False)
    is_default_billing = BooleanField(default=False)

    created_at = DateTimeField(default=datetime.utcnow)
    updated_at = DateTimeField(default=datetime.utcnow)

    meta = {
        'ordering': ['-created_at'],
    }

    def save(self, *args, **kwargs):
        self.updated_at = datetime.utcnow()
        return super().save(*args, **kwargs)
