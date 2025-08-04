# products/models.py

from mongoengine import (
    Document,
    StringField,
    FloatField,
    ListField,
    DictField,
    BooleanField,
    IntField,
)


class Product(Document):
    _id = StringField(primary_key=True)  # Always a string
    product_name = StringField(max_length=255)
    category = StringField(max_length=100)
    description = StringField()
    price = FloatField()
    ingredients = ListField(StringField(max_length=255))
    images = ListField(StringField())
    variations = ListField(DictField())
    weight = FloatField(null=True, blank=True)
    dimensions = StringField(max_length=255, null=True, blank=True)
    benefits = ListField(StringField(max_length=255))
    scent_profile = StringField(max_length=255, null=True, blank=True)
    variants = ListField(DictField(), default=list)
    tags = ListField(StringField(max_length=255))
    availability = BooleanField(default=True)
    inventory = IntField(default=0)
    reserved_inventory = IntField(default=0)
    average_rating = FloatField(default=0.0)
    review_count = IntField(default=0)

    meta = {
        "indexes": [
            "category",
            "tags",
            "product_name",
        ]
    }

    def __str__(self):
        return self.product_name

    @property
    def id_str(self):
        return str(self._id)


class Category(Document):
    _id = StringField(primary_key=True)  # Use string primary key for references
    name = StringField(max_length=100, required=True, unique=True)
    description = StringField(null=True, blank=True)

    def __str__(self):
        return self.name
