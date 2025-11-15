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
    def validate_code(self, value):
        normalized = value.upper()
        qs = Discount.objects(code=normalized)
        if self.instance:
            qs = qs.filter(id__ne=self.instance.id)
        if qs.first():
            raise serializers.ValidationError("Discount code must be unique.")
        return normalized

    class Meta:
        model = Discount
        fields = "__all__"


class CategorySerializer(DocumentSerializer):
    class Meta:
        model = Category
        fields = "__all__"

