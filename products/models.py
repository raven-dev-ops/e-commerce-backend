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
from mongoengine.queryset.manager import queryset_manager
from django.utils.text import slugify


class Product(Document):
    _id = StringField(primary_key=True)  # Always a string
    product_name = StringField(max_length=255)
    slug = StringField(max_length=255, unique=True)
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
    approved_review_count = IntField(default=0)
    is_deleted = BooleanField(default=False)

    meta = {
        "indexes": [
            "category",
            "tags",
            "product_name",
            "slug",
        ]
    }

    @queryset_manager
    def objects(doc_cls, queryset):
        return queryset.filter(is_deleted=False)

    @queryset_manager
    def all_objects(doc_cls, queryset):
        return queryset

    def __str__(self):
        return self.product_name

    @property
    def id_str(self):
        return str(self._id)

    def save(self, *args, **kwargs):
        if not self.slug and self.product_name:
            base_slug = slugify(self.product_name)
            slug = base_slug
            counter = 1
            while Product.objects(slug=slug).first() is not None:
                slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = slug
        return super().save(*args, **kwargs)

    def add_review(self, rating: int, status: str) -> None:
        """Increment review counts and update average rating."""
        self.review_count += 1
        if status == "approved":
            if self.approved_review_count == 0:
                self.average_rating = rating
            else:
                self.average_rating = (
                    (self.average_rating * self.approved_review_count) + rating
                ) / (self.approved_review_count + 1)
            self.approved_review_count += 1
        self.save()

    def update_review(
        self,
        old_rating: int,
        new_rating: int,
        old_status: str,
        new_status: str,
    ) -> None:
        """Update rating averages when a review changes."""
        if old_status == "approved" and new_status == "approved":
            if self.approved_review_count > 0:
                self.average_rating = (
                    (self.average_rating * self.approved_review_count)
                    - old_rating
                    + new_rating
                ) / self.approved_review_count
        elif old_status != "approved" and new_status == "approved":
            if self.approved_review_count == 0:
                self.average_rating = new_rating
            else:
                self.average_rating = (
                    (self.average_rating * self.approved_review_count) + new_rating
                ) / (self.approved_review_count + 1)
            self.approved_review_count += 1
        elif old_status == "approved" and new_status != "approved":
            if self.approved_review_count > 1:
                self.average_rating = (
                    (self.average_rating * self.approved_review_count) - old_rating
                ) / (self.approved_review_count - 1)
            else:
                self.average_rating = 0.0
            self.approved_review_count -= 1
        self.save()

    def remove_review(self, rating: int, status: str) -> None:
        """Decrement review counts and update rating on deletion."""
        if status == "approved":
            if self.approved_review_count > 1:
                self.average_rating = (
                    (self.average_rating * self.approved_review_count) - rating
                ) / (self.approved_review_count - 1)
            else:
                self.average_rating = 0.0
            self.approved_review_count -= 1
        self.review_count -= 1
        self.save()

    def delete(self, *args, **kwargs):
        self.is_deleted = True
        self.save()

    def restore(self):
        self.is_deleted = False
        self.save()


class Category(Document):
    _id = StringField(primary_key=True)  # Use string primary key for references
    name = StringField(max_length=100, required=True, unique=True)
    description = StringField(null=True, blank=True)

    def __str__(self):
        return self.name
