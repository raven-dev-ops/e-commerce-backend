from rest_framework_mongoengine.serializers import DocumentSerializer

from cart.models import Cart, CartItem


class CartItemSerializer(DocumentSerializer):
    class Meta:
        model = CartItem
        fields = ("id", "product_id", "quantity")


class CartSerializer(DocumentSerializer):
    class Meta:
        model = Cart
        fields = ("id", "user")

