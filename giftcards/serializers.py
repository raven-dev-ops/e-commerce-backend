from rest_framework import serializers
from .models import GiftCard


class GiftCardSerializer(serializers.ModelSerializer):
    class Meta:
        model = GiftCard
        fields = [
            "id",
            "code",
            "amount",
            "balance",
            "is_active",
            "created_at",
            "redeemed_at",
        ]
        read_only_fields = [
            "id",
            "code",
            "balance",
            "is_active",
            "created_at",
            "redeemed_at",
        ]


class GiftCardPurchaseSerializer(serializers.Serializer):
    amount = serializers.DecimalField(max_digits=10, decimal_places=2)


class GiftCardRedeemSerializer(serializers.Serializer):
    code = serializers.CharField()
