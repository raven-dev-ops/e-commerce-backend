"""Admin configuration for the discounts app."""

from django_mongoengine import mongo_admin
from django_mongoengine.mongo_admin.sites import DocumentMetaWrapper

from .models import Discount
from products.models import Category, Product


class DiscountAdmin(mongo_admin.DocumentAdmin):
    """Admin configuration for managing discount rules."""

    list_display = (
        "code",
        "discount_type",
        "value",
        "is_active",
        "valid_from",
        "valid_to",
    )
    search_fields = ("code",)
    ordering = ("-valid_from",)


class DefaultManager:
    def __init__(self, doc):
        self.doc = doc

    def get_queryset(self):
        return self.doc.objects


for document in (Product, Category, Discount):
    # Ensure referenced documents expose Django-like `_meta` attributes
    document._meta = DocumentMetaWrapper(document)
    document._default_manager = DefaultManager(document)

mongo_admin.site.register(Discount, DiscountAdmin)
