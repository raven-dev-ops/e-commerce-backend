# products/serializers.py

from rest_framework_mongoengine.serializers import DocumentSerializer
from rest_framework import serializers
from products.models import Product

class ProductSerializer(DocumentSerializer):
    id = serializers.CharField(read_only=True)  # MongoDB ObjectId as string
    _id = serializers.SerializerMethodField()   # Always a string for compatibility

    product_name = serializers.CharField(max_length=255)
    category = serializers.CharField(max_length=100)
    description = serializers.CharField()
    price = serializers.DecimalField(max_digits=10, decimal_places=2)
    ingredients = serializers.ListField(child=serializers.CharField())
    images = serializers.ListField(child=serializers.CharField(), required=False)
    variations = serializers.ListField(child=serializers.DictField(), required=False)
    weight = serializers.FloatField(required=False, allow_null=True)
    dimensions = serializers.CharField(max_length=255, required=False, allow_null=True, allow_blank=True)
    benefits = serializers.ListField(child=serializers.CharField())
    scent_profile = serializers.CharField(max_length=255, required=False, allow_null=True, allow_blank=True)
    variants = serializers.ListField(child=serializers.DictField(), required=False)
    tags = serializers.ListField(child=serializers.CharField(), required=False)
    availability = serializers.BooleanField(default=True)
    inventory = serializers.IntegerField()
    reserved_inventory = serializers.IntegerField()
    average_rating = serializers.FloatField(read_only=True)
    review_count = serializers.IntegerField(read_only=True)

    def get__id(self, obj):
        # Ensures _id is always a string, no matter how it's stored
        return str(obj.id)

    class Meta:
        model = Product
        fields = '__all__'  # include all model/document fields + id + _id
        document = Product  # for MongoEngine compatibility
