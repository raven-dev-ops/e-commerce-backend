from mongoengine import Document, StringField, FloatField, BooleanField, DateTimeField, IntField, ListField, ReferenceField
from products.models import Product, Category


class Discount(Document):
    code = StringField(unique=True, required=True)
    discount_type = StringField(choices=['percentage', 'fixed'], required=True)
    value = FloatField(required=True)
    is_active = BooleanField(default=True)
    valid_from = DateTimeField(null=True)
    valid_to = DateTimeField(null=True)
    usage_limit = IntField(null=True)
    times_used = IntField(default=0)
    min_purchase_amount = FloatField(null=True)
    target_products = ListField(ReferenceField(Product), null=True)
    target_categories = ListField(ReferenceField(Category), null=True)
    is_automatic = BooleanField(default=False)
    is_free_shipping = BooleanField(default=False)
    category = ReferenceField(Category, null=True)