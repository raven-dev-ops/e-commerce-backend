# src/authentication/serializers.py

from rest_framework import serializers
from django.contrib.auth import get_user_model
from authentication.models import Address
from rest_framework_mongoengine.serializers import DocumentSerializer
from dj_rest_auth.registration.serializers import SocialLoginSerializer
from allauth.socialaccount.providers.google.views import GoogleOAuth2Adapter
from allauth.socialaccount.providers.oauth2.client import OAuth2Client


class AddressSerializer(DocumentSerializer):
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
    You can remove this entire class if you want dj-rest-auth to use
    its built-in RegisterSerializer instead.
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


# ——— Custom Social‑Login Serializer ———


class CustomSocialLoginSerializer(SocialLoginSerializer):
    """
    Wraps allauth's OAuth2Client but only passes each init‑arg once,
    preventing the 'multiple values for argument "scope_delimiter"' error.
    """

    adapter_class = GoogleOAuth2Adapter
    client_class = OAuth2Client
    callback_url = None  # e.g. your front‑end redirect URI

    def get_client(self, request, adapter):
        app = adapter.get_provider().get_app(request)
        return self.client_class(
            request=request,
            client_id=app.client_id,
            client_secret=app.secret,
            access_token_url=adapter.access_token_url,
            authorize_url=adapter.authorize_url,
            callback_url=self.callback_url,
        )
