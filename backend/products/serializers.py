from rest_framework_mongoengine.serializers import DocumentSerializer
from rest_framework import serializers


class ProductSerializer(DocumentSerializer):

    id = serializers.CharField(read_only=True) # Use id to match mongoengine's _id
    product_name = serializers.CharField(max_length=255)
    category = serializers.CharField(max_length=100)
    description = serializers.CharField()
    price = serializers.DecimalField(max_digits=10, decimal_places=2)
    ingredients = serializers.ListField(child=serializers.CharField())
    benefits = serializers.ListField(child=serializers.CharField())
    scent_profile = serializers.CharField(max_length=100, allow_null=True, allow_blank=True)
    variants = serializers.ListField(child=serializers.CharField(), required=False) # Assuming variants are strings, adjust if needed
    tags = serializers.ListField(child=serializers.CharField(), required=False)
    inventory = serializers.IntegerField()
    reserved_inventory = serializers.IntegerField()
    average_rating = serializers.FloatField(read_only=True)
    review_count = serializers.IntegerField(read_only=True)