from rest_framework import serializers
from reviews.models import Review
from products.models import Product
from django.contrib.auth import get_user_model
from rest_framework_mongoengine.serializers import DocumentSerializer


class ReviewSerializer(DocumentSerializer):
    product = serializers.PrimaryKeyRelatedField(queryset=Product.objects.all())
    user = serializers.PrimaryKeyRelatedField(queryset=User.objects.all())

    class Meta:
        document = Review
        fields = '__all__'