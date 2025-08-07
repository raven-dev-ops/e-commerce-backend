# cart/models.py

from mongoengine import (
    Document,
    ReferenceField,
    IntField,
    DateTimeField,
    CASCADE,
    StringField,
    BooleanField,
)
from mongoengine.queryset.manager import queryset_manager
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
    is_deleted = BooleanField(default=False)

    @queryset_manager
    def objects(doc_cls, queryset):
        return queryset.filter(is_deleted=False)

    @queryset_manager
    def all_objects(doc_cls, queryset):
        return queryset

    def __str__(self):
        return f"Cart {str(self.id)} for user {self.user.id}"

    def save(self, *args, **kwargs):
        self.updated_at = datetime.utcnow()
        return super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        self.is_deleted = True
        self.save()

    def restore(self):
        self.is_deleted = False
        self.save()


class CartItem(Document):
    cart = ReferenceField(Cart, reverse_delete_rule=CASCADE)
    product_id = StringField(required=True)
    quantity = IntField(default=1, min_value=1)

    def __str__(self):
        return f"{self.quantity} x {self.product_id}"
