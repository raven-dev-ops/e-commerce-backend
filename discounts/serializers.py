# discoounts/serializers.py

from rest_framework import serializers
from rest_framework_mongoengine.serializers import DocumentSerializer
from products.models import Product, Category
from discounts.models import Discount
from reviews.models import Review


class ProductSerializer(DocumentSerializer):
    class Meta:
        model = Product
        fields = "__all__"


class ReviewSerializer(DocumentSerializer):
    product = ProductSerializer(read_only=True)
    product_id = serializers.CharField(write_only=True)

    class Meta:
        model = Review
        fields = "__all__"


class DiscountSerializer(DocumentSerializer):
    class Meta:
        model = Discount
        fields = "__all__"


class CategorySerializer(DocumentSerializer):
    class Meta:
        model = Category
        fields = "__all__"
