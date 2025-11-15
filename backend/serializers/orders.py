from rest_framework import serializers

from orders.models import Order, OrderItem
from backend.serializers.authentication import AddressSerializer


class OrderItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderItem
        fields = ["id", "product_name", "quantity", "unit_price"]


class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)
    shipping_address = AddressSerializer(read_only=True)
    billing_address = AddressSerializer(read_only=True)

    class Meta:
        model = Order
        fields = [
            "id",
            "user",
            "created_at",
            "total_price",
            "currency",
            "shipping_cost",
            "tax_amount",
            "payment_intent_id",
            "status",
            "shipping_address",
            "billing_address",
            "shipped_date",
            "discount_code",
            "discount_type",
            "discount_value",
            "discount_amount",
            "is_gift",
            "gift_message",
            "items",
        ]
        read_only_fields = [
            "id",
            "user",
            "created_at",
            "payment_intent_id",
            "status",
            "items",
            "currency",
        ]

