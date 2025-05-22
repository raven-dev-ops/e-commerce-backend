from django_mongoengine_filter import FilterSet
from .models import Product

class ProductFilter(FilterSet):
    class Meta:
        model = Product
        fields = ['category', 'price', 'tags']