# users/models.py

from mongoengine import Document, StringField, EmailField, ListField, ReferenceField
from django.utils.translation import gettext_lazy as _

class User(Document):
    """
    Custom MongoEngine User model replacing Django's AbstractUser.
    """
    username = StringField(required=True, unique=True, max_length=150, verbose_name=_("username"))
    email = EmailField(required=True, unique=True, verbose_name=_("email address"))
    password = StringField(required=True, verbose_name=_("password"))
    first_name = StringField(max_length=30, verbose_name=_("first name"))
    last_name = StringField(max_length=150, verbose_name=_("last name"))

    meta = {
        'collection': 'user',  # MongoDB collection name
        'indexes': ['email', 'username'],
        'ordering': ['username']
    }

    def __str__(self):
        return self.username
