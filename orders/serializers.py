from rest_framework import serializers
from orders.models import Cart, CartItem, Order, OrderItem
from authentication.serializers import AddressSerializer
from rest_framework_mongoengine.serializers import DocumentSerializer
from discounts.serializers import DiscountSerializer
class CartItemSerializer(serializers.Serializer):
    product_id = serializers.CharField(max_length=24)  # Assuming ObjectId is 24 chars
    quantity = serializers.IntegerField(min_value=1)

class CartSerializer(serializers.Serializer):
    user = serializers.IntegerField()  # Assuming Django user ID is an integer
    items = CartItemSerializer(many=True)
    discount = DiscountSerializer(read_only=True, allow_null=True)

    def create(self, validated_data):
        items_data = validated_data.pop('items')
        cart = Cart.objects.create(**validated_data)
        for item_data in items_data:
            cart.items.append(CartItem(**item_data))
        cart.save()
        return cart

    def update(self, instance, validated_data):
        items_data = validated_data.pop('items')
        instance.user = validated_data.get('user', instance.user)
        # Clear existing items and add updated ones - adjust logic if you need to merge/update
        instance.items = []
        for item_data in items_data:
            instance.items.append(CartItem(**item_data))
        instance.save()
        return instance

class OrderItemSerializer(DocumentSerializer):
    class Meta:
        model = OrderItem
        fields = ['product', 'quantity', 'price']

class OrderSerializer(DocumentSerializer):
    items = OrderItemSerializer(many=True, read_only=True)
    shipping_address = AddressSerializer(read_only=True)
    billing_address = AddressSerializer(read_only=True)
    class Meta:
        model = Order        
        fields = ['user', 'items', 'total_price', 'shipping_cost', 'tax_amount', 'shipping_address', 'billing_address', 'created_at', 'updated_at', 'discount_code', 'discount_type', 'discount_value', 'discount_amount']
