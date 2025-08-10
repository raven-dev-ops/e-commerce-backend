from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import GiftCard
from .serializers import (
    GiftCardPurchaseSerializer,
    GiftCardRedeemSerializer,
    GiftCardSerializer,
)


class GiftCardViewSet(viewsets.ModelViewSet):
    queryset = GiftCard.objects.all()
    serializer_class = GiftCardSerializer
    permission_classes = [IsAuthenticated]

    def create(self, request, *args, **kwargs):
        serializer = GiftCardPurchaseSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        amount = serializer.validated_data["amount"]
        card = GiftCard.objects.create(amount=amount, balance=amount)
        output = GiftCardSerializer(card)
        return Response(output.data, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=["post"])
    def redeem(self, request, *args, **kwargs):
        serializer = GiftCardRedeemSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        card = get_object_or_404(
            GiftCard, code=serializer.validated_data["code"], is_active=True
        )
        card.is_active = False
        card.balance = 0
        card.redeemed_at = timezone.now()
        card.redeemed_by = request.user
        card.save(update_fields=["is_active", "balance", "redeemed_at", "redeemed_by"])
        output = GiftCardSerializer(card)
        return Response(output.data)
