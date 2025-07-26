# authentication/serializers.py

from rest_framework import serializers
from django.contrib.auth.models import User
from authentication.models import Address
from rest_framework_mongoengine.serializers import DocumentSerializer

# ——— your existing serializers ———

class AddressSerializer(DocumentSerializer):
    class Meta:
        model = Address
        fields = (
            'user', 'street', 'city', 'state', 'country', 'zip_code',
            'is_default_shipping', 'is_default_billing'
        )
        read_only_fields = ('user',)


class UserRegistrationSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('username', 'email', 'password')
        extra_kwargs = {'password': {'write_only': True}}

    def create(self, validated_data):
        return User.objects.create_user(**validated_data)


class UserProfileSerializer(serializers.ModelSerializer):
    default_shipping_address = serializers.SerializerMethodField()
    default_billing_address  = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            'username', 'email', 'first_name', 'last_name',
            'date_joined', 'last_login',
            'default_shipping_address', 'default_billing_address'
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


# ——— custom social‑login serializer ———

from dj_rest_auth.registration.serializers import SocialLoginSerializer
from allauth.socialaccount.providers.google.views import GoogleOAuth2Adapter
from allauth.socialaccount.providers.oauth2.client import OAuth2Client

class CustomSocialLoginSerializer(SocialLoginSerializer):
    """
    Uses allauth's OAuth2Client but only supplies each init‑arg once,
    so we don’t get “multiple values for argument 'scope_delimiter'”.
    """
    adapter_class = GoogleOAuth2Adapter
    client_class  = OAuth2Client
    callback_url  = None  # or your front‑end callback

    def get_client(self, request, adapter):
        # build the client with only the required args
        app = adapter.get_provider().get_app(request)
        return self.client_class(
            request=request,
            client_id=app.client_id,
            client_secret=app.secret,
            access_token_url=adapter.access_token_url,
            authorize_url=adapter.authorize_url,
            callback_url=self.callback_url,
        )
