from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.utils import timezone
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
        fields = ("username", "email", "password", "marketing_opt_in")
        extra_kwargs = {
            "password": {"write_only": True},
            "marketing_opt_in": {"required": False},
        }

    def create(self, validated_data):
        if validated_data.get("marketing_opt_in"):
            validated_data["marketing_opt_in_at"] = timezone.now()
            validated_data["marketing_opt_out_at"] = None
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
            "marketing_opt_in",
            "marketing_opt_in_at",
            "marketing_opt_out_at",
            "default_shipping_address",
            "default_billing_address",
        )
        read_only_fields = ("marketing_opt_in_at", "marketing_opt_out_at")

    def update(self, instance, validated_data):
        marketing_opt_in = validated_data.pop("marketing_opt_in", None)
        if marketing_opt_in is not None and marketing_opt_in != instance.marketing_opt_in:
            instance.marketing_opt_in = marketing_opt_in
            now = timezone.now()
            if marketing_opt_in:
                instance.marketing_opt_in_at = now
                instance.marketing_opt_out_at = None
            else:
                instance.marketing_opt_out_at = now
        return super().update(instance, validated_data)

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
