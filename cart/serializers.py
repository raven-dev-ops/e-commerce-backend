# cart/serializers.py

from rest_framework_mongoengine.serializers import DocumentSerializer

from .models import Cart, CartItem


class CartItemSerializer(DocumentSerializer):
    class Meta:
        model = CartItem
        fields = ("id", "product_id", "quantity")


class CartSerializer(DocumentSerializer):
    class Meta:
        model = Cart
        fields = ("id", "user_id")
