from rest_framework_mongoengine.serializers import DocumentSerializer
from rest_framework import serializers
from django.contrib.auth import get_user_model

from reviews.models import Review


class ReviewSerializer(DocumentSerializer):
    user_id = serializers.IntegerField(write_only=True)
    user = serializers.SerializerMethodField(read_only=True)

    def get_user(self, obj):
        User = get_user_model()
        try:
            user = User.objects.get(pk=obj.user_id)
            return user.username
        except User.DoesNotExist:
            return None

    class Meta:
        model = Review
        fields = [
            "id",
            "user_id",
            "user",
            "product",
            "rating",
            "comment",
            "status",
            "created_at",
        ]

