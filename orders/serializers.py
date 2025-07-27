# orders/serializers.py

from rest_framework import serializers
from orders.models import Order, OrderItem  # Django ORM models
from authentication.serializers import AddressSerializer

# OrderItem uses Django ORM ModelSerializer
class OrderItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderItem
        fields = ['id', 'product_name', 'quantity', 'unit_price']

# Order uses Django ORM ModelSerializer, nests items and addresses
class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)
    shipping_address = AddressSerializer(read_only=True)
    billing_address = AddressSerializer(read_only=True)

    class Meta:
        model = Order
        fields = [
            'id',
            'user',
            'created_at',
            'total_price',
            'shipping_cost',
            'tax_amount',
            'payment_intent_id',
            'status',
            'shipping_address',
            'billing_address',
            'shipped_date',
            'discount_code',
            'discount_type',
            'discount_value',
            'discount_amount',
            'items',
        ]
        read_only_fields = ['id', 'user', 'created_at', 'payment_intent_id', 'status', 'items']
