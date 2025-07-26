# authentication/serializers.py

from rest_framework import serializers
from django.contrib.auth.models import User
from authentication.models import Address
from rest_framework_mongoengine.serializers import DocumentSerializer

# dj-rest-auth / allauth imports
from dj_rest_auth.registration.serializers import SocialLoginSerializer
from allauth.socialaccount.providers.google.views import GoogleOAuth2Adapter
from allauth.socialaccount.providers.oauth2.client import OAuth2Client


class AddressSerializer(DocumentSerializer):
    class Meta:
        model = Address
        fields = (
            'user',
            'street',
            'city',
            'state',
            'country',
            'zip_code',
            'is_default_shipping',
            'is_default_billing',
        )
        read_only_fields = ('user',)


class UserRegistrationSerializer(serializers.ModelSerializer):
    """Used by dj-rest-auth for email/password sign‑up."""
    class Meta:
        model = User
        fields = ('username', 'email', 'password')
        extra_kwargs = {'password': {'write_only': True}}

    def create(self, validated_data):
        return User.objects.create_user(**validated_data)


class UserProfileSerializer(serializers.ModelSerializer):
    """Expose user profile + default addresses."""
    default_shipping_address = serializers.SerializerMethodField()
    default_billing_address = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            'username',
            'email',
            'first_name',
            'last_name',
            'date_joined',
            'last_login',
            'default_shipping_address',
            'default_billing_address',
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
    Fixes the OAuth2Client __init__ signature clash by
    constructing the client with explicit keyword-only args,
    so 'scope_delimiter' is not passed twice.
    """
    adapter_class = GoogleOAuth2Adapter  # swap out for any other provider
    client_class = OAuth2Client
    callback_url = None  # or your front‑end callback URI

    def get_client(self, request, adapter):
        # Grab the App credentials from allauth
        app = adapter.get_provider().get_app(request)
        return self.client_class(
            request=request,
            consumer_key=app.client_id,
            consumer_secret=app.secret,
            access_token_url=adapter.access_token_url,
            callback_url=self.callback_url,
        )
