from rest_framework import serializers
from .models import ReferralCode


class ReferralCodeSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReferralCode
        fields = ["id", "code", "created_by", "usage_count", "created_at"]
        read_only_fields = ["id", "code", "created_by", "usage_count", "created_at"]


class ReferralCodeCreateSerializer(serializers.Serializer):
    pass


class ReferralCodeTrackSerializer(serializers.Serializer):
    code = serializers.CharField()
