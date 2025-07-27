# reviews/models.py

from mongoengine import Document, StringField, IntField, DateTimeField, ReferenceField
from datetime import datetime
from products.models import Product
from django.conf import settings

class Review(Document):
    user_id = IntField(required=True)  # Store Django user PK
    product = ReferenceField(Product, required=True)
    rating = IntField(min_value=1, max_value=5, required=True)
    comment = StringField(required=False)
    status = StringField(choices=['pending', 'approved', 'rejected'], default='pending')
    created_at = DateTimeField(default=datetime.utcnow)

    @property
    def user(self):
        # Lazy user lookup for convenience
        from users.models import User  # Import here to avoid circular import
        try:
            return User.objects.get(pk=self.user_id)
        except User.DoesNotExist:
            return None

    meta = {
        'indexes': [
            'user_id',
            'product',
            'status',
        ]
    }

    def __str__(self):
        return f"Review by User {self.user_id} for {self.product}"
