from .models import Review
from authentication.models import User
from .models import Product
from djangorestframework_mongoengine.serializers import DocumentSerializer
from rest_framework_mongoengine.serializers import DocumentSerializer
from rest_framework import serializers
from django.contrib.auth import get_user_model

class ReviewSerializer(DocumentSerializer):
    user_id = serializers.IntegerField(write_only=True) # Accept user_id for writing
    user = serializers.SerializerMethodField(read_only=True) # Display username for reading

    def get_user(self, obj):
        User = get_user_model()
        try:
            user = User.objects.get(pk=obj.user_id)
            return user.username
        except User.DoesNotExist:
            return None # Or handle as appropriate if user doesn't exist

    class Meta:
        model = Review