from rest_framework import serializers
from django.contrib.auth.models import User
from authentication.models import Address

class UserRegistrationSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('username', 'email', 'password')
        extra_kwargs = {'password': {'write_only': True}}


class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = User        
        fields = ('username', 'email', 'first_name', 'last_name', 'date_joined', 'last_login', 'default_shipping_address', 'default_billing_address')

    def get_default_shipping_address(self, obj):
        """
        Returns the user's default shipping address.
        """
        try:
            address = Address.objects.get(user=obj, is_default_shipping=True)
            return AddressSerializer(address).data
        except Address.DoesNotExist:
            return None

    def get_default_billing_address(self, obj):
        """
        Returns the user's default billing address.
        """
from rest_framework_mongoengine.serializers import DocumentSerializer
class AddressSerializer(DocumentSerializer):
    class Meta:
        model = Address
        fields = ('user', 'street', 'city', 'state', 'country', 'zip_code', 'is_default_shipping', 'is_default_billing')
        read_only_fields = ('user',)