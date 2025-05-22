from rest_framework import serializers
from django.contrib.auth.models import User
from authentication.models import Address
from rest_framework_mongoengine.serializers import DocumentSerializer


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
        user = User.objects.create_user(**validated_data)
        return user


class UserProfileSerializer(serializers.ModelSerializer):
    default_shipping_address = serializers.SerializerMethodField()
    default_billing_address = serializers.SerializerMethodField()

    class Meta:
        model = User        
        fields = (
            'username', 'email', 'first_name', 'last_name',
            'date_joined', 'last_login',
            'default_shipping_address', 'default_billing_address'
        )

    def get_default_shipping_address(self, obj):
        try:
            address = Address.objects.get(user=obj.id, is_default_shipping=True)
            return AddressSerializer(address).data
        except Address.DoesNotExist:
            return None

    def get_default_billing_address(self, obj):
        try:
            address = Address.objects.get(user=obj.id, is_default_billing=True)
            return AddressSerializer(address).data
        except Address.DoesNotExist:
            return None
