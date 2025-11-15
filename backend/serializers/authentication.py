from rest_framework import serializers
from django.contrib.auth import get_user_model
from dj_rest_auth.registration.serializers import SocialLoginSerializer

from authentication.models import Address


class AddressSerializer(serializers.ModelSerializer):
    class Meta:
        model = Address
        fields = (
            "user",
            "street",
            "city",
            "state",
            "country",
            "zip_code",
            "is_default_shipping",
            "is_default_billing",
        )
        read_only_fields = ("user",)


User = get_user_model()


class UserRegistrationSerializer(serializers.ModelSerializer):
    """
    Custom registration serializer (optional).
    """

    class Meta:
        model = User
        fields = ("username", "email", "password")
        extra_kwargs = {"password": {"write_only": True}}

    def create(self, validated_data):
        return User.objects.create_user(**validated_data)


class UserProfileSerializer(serializers.ModelSerializer):
    default_shipping_address = serializers.SerializerMethodField()
    default_billing_address = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            "username",
            "email",
            "first_name",
            "last_name",
            "date_joined",
            "last_login",
            "default_shipping_address",
            "default_billing_address",
        )

    def get_default_shipping_address(self, obj):
        try:
            addr = Address.objects.get(user=obj.id, is_default_shipping=True)
            return AddressSerializer(addr).data
        except Address.DoesNotExist:
            return None

    def get_default_billing_address(self, obj):
        try:
            addr = Address.objects.get(user=obj.id, is_default_billing=True)
            return AddressSerializer(addr).data
        except Address.DoesNotExist:
            return None


class CustomSocialLoginSerializer(SocialLoginSerializer):
    """
    Placeholder custom social-login serializer so the
    REST_AUTH_SERIALIZERS setting resolves correctly.
    """

    # You can extend this later to add custom behavior.
    pass
