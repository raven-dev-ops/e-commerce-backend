# cart/models.py

from mongoengine import (
    Document, ReferenceField, IntField, DateTimeField, CASCADE, StringField
)
from datetime import datetime
from products.models import Product

class Cart(Document):
    user_id = StringField(required=True)  # Store user PK as string for portability
    created_at = DateTimeField(default=datetime.utcnow)
    updated_at = DateTimeField(default=datetime.utcnow)

    def __str__(self):
        return f"Cart {str(self.id)} for user {self.user_id}"

    def save(self, *args, **kwargs):
        self.updated_at = datetime.utcnow()
        return super().save(*args, **kwargs)

class CartItem(Document):
    cart = ReferenceField(Cart, reverse_delete_rule=CASCADE)
    product = ReferenceField(Product, reverse_delete_rule=CASCADE)
    quantity = IntField(default=1, min_value=1)

    def __str__(self):
        return f"{self.quantity} x {self.product.product_name}"
