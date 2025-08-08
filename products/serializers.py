from rest_framework_mongoengine.serializers import DocumentSerializer
from rest_framework import serializers
from products.models import Product
from bson import ObjectId


class ProductSerializer(DocumentSerializer):
    # Expose _id as a string for the frontend
    _id = serializers.CharField(read_only=True)

    product_name = serializers.CharField(max_length=255)
    slug = serializers.CharField(read_only=True)
    category = serializers.CharField(max_length=100)
    description = serializers.CharField()
    price = serializers.DecimalField(max_digits=10, decimal_places=2)
    ingredients = serializers.ListField(child=serializers.CharField())
    images = serializers.ListField(
        child=serializers.CharField(), required=False, read_only=True
    )
    uploaded_images = serializers.ListField(
        child=serializers.ImageField(), write_only=True, required=False
    )
    variations = serializers.ListField(child=serializers.DictField(), required=False)
    weight = serializers.FloatField(required=False, allow_null=True)
    dimensions = serializers.CharField(
        max_length=255, required=False, allow_null=True, allow_blank=True
    )
    benefits = serializers.ListField(child=serializers.CharField())
    scent_profile = serializers.CharField(
        max_length=255, required=False, allow_null=True, allow_blank=True
    )
    variants = serializers.ListField(child=serializers.DictField(), required=False)
    tags = serializers.ListField(child=serializers.CharField(), required=False)
    availability = serializers.BooleanField(default=True)
    inventory = serializers.IntegerField()
    reserved_inventory = serializers.IntegerField()
    average_rating = serializers.FloatField(read_only=True)
    review_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Product
        fields = [
            "_id",
            "product_name",
            "slug",
            "category",
            "description",
            "price",
            "ingredients",
            "images",
            "variations",
            "weight",
            "dimensions",
            "benefits",
            "scent_profile",
            "variants",
            "tags",
            "availability",
            "inventory",
            "reserved_inventory",
            "average_rating",
            "review_count",
            "uploaded_images",
        ]

    def create(self, validated_data):
        validated_data["_id"] = str(ObjectId())
        validated_data.pop("uploaded_images", None)
        return super().create(validated_data)

    def update(self, instance, validated_data):
        validated_data.pop("uploaded_images", None)
        return super().update(instance, validated_data)
