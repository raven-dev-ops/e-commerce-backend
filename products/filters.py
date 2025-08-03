# product/filters.py

from django_mongoengine_filter import FilterSet
from .models import Product


class ProductFilter(FilterSet):
    class Meta:
        model = Product
        fields = {
            "category": ["exact", "in"],
            "price": ["exact", "gte", "lte"],
            "tags": ["exact", "in"],
        }
