from mongoengine import Document, StringField, FloatField, ListField, DictField, BooleanField, IntField, fields

class Product(Document):
    product_name = StringField(max_length=255)
    category = StringField(max_length=100)
    description = StringField()
    price = FloatField()
    ingredients = ListField(StringField(max_length=255))
    images = fields.ListField(fields.StringField())
    variations = fields.ListField(fields.DictField())
    weight = fields.FloatField(required=False)
    dimensions = fields.StringField(max_length=255, required=False)
    benefits = ListField(StringField(max_length=255))
    scent_profile = StringField(max_length=255, required=False)
    variants = ListField(DictField(), default=list)
    tags = ListField(StringField(max_length=255))
    availability = BooleanField(default=True)
    inventory = IntField(default=0)
    reserved_inventory = IntField(default=0)
    average_rating = FloatField(default=0.0)
    review_count = IntField(default=0)

    def __str__(self):
        return self.product_name

class Category(Document):
    name = StringField(max_length=100, required=True)
    description = StringField(required=False)

