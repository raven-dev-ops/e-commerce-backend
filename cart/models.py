# cart/models.py

from mongoengine import (
    Document,
    ReferenceField,
    IntField,
    DateTimeField,
    CASCADE,
    StringField,
)
from datetime import datetime


class UserRef(Document):
    id = IntField(primary_key=True)

    def __str__(self):
        return str(self.id)


def get_or_create_user_ref(user):
    user_ref = UserRef.objects(id=user.id).first()
    if not user_ref:
        user_ref = UserRef(id=user.id)
        user_ref.save()
    return user_ref


class Cart(Document):
    user = ReferenceField(UserRef, reverse_delete_rule=CASCADE, required=True)
    created_at = DateTimeField(default=datetime.utcnow)
    updated_at = DateTimeField(default=datetime.utcnow)

    def __str__(self):
        return f"Cart {str(self.id)} for user {self.user.id}"

    def save(self, *args, **kwargs):
        self.updated_at = datetime.utcnow()
        return super().save(*args, **kwargs)


class CartItem(Document):
    cart = ReferenceField(Cart, reverse_delete_rule=CASCADE)
    product_id = StringField(required=True)
    quantity = IntField(default=1, min_value=1)

    def __str__(self):
        return f"{self.quantity} x {self.product_id}"
