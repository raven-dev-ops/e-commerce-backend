from mongoengine import Document, StringField, ReferenceField, BooleanField
from users.models import User

class Address(Document):
    user = ReferenceField('User', required=True)
    street = StringField(required=True)
    is_default_shipping = BooleanField(default=False)
    is_default_billing = BooleanField(default=False)
    city = StringField(required=True)
    state = StringField()  # State might be optional depending on country
    country = StringField(required=True)
    zip_code = StringField(required=True)

