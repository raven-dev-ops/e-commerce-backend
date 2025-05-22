from django.db import models
from django.conf import settings
from products.models import Product
from mongoengine import Document, EmbeddedDocument, fields
from discounts.models import Discount
from authentication.models import Address

class CartItem(EmbeddedDocument):
    product_id = fields.StringField(required=True) # To store the MongoDB ObjectId as a string
    quantity = fields.IntField(required=True, min_value=1)

class Cart(Document):
    user = fields.IntField(required=True) # To store the Django user ID
    items = fields.ListField(fields.EmbeddedDocumentField(CartItem))
    discount = fields.ReferenceField(Discount, null=True)


ORDER_STATUS_CHOICES = [
    ('pending', 'Pending Payment'),
    ('processing', 'Processing'),
    ('shipped', 'Shipped'),
    ('delivered', 'Delivered'),
    ('canceled', 'Canceled'),
    ('failed', 'Payment Failed'),
]

class OrderItem(EmbeddedDocument):
    product_id = fields.StringField(required=True)  # To store the MongoDB ObjectId as a string
    quantity = fields.IntField(required=True, min_value=1)


class Order(Document):
    user = fields.IntField(required=True) # To store the Django user ID
    created_at = fields.DateTimeField(required=True)
    total_price = fields.DecimalField(required=True)
    shipping_cost = fields.DecimalField(default=0.0)
    tax_amount = fields.DecimalField(default=0.0)
    payment_intent_id = fields.StringField() # To store the Stripe PaymentIntent ID
    status = fields.StringField(choices=ORDER_STATUS_CHOICES, default='pending')
    shipping_address = fields.ReferenceField(Address, required=False)
    billing_address = fields.ReferenceField(Address, required=False)
    discount_code = fields.StringField(null=True)
    shipped_date = fields.DateTimeField(null=True)
    discount_type = fields.StringField(choices=['percentage', 'fixed'], null=True)
    discount_value = fields.FloatField(null=True)
    discount_amount = fields.FloatField(null=True)
    items = fields.ListField(fields.EmbeddedDocumentField(OrderItem))