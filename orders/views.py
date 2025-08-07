# orders/views.py

from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
import logging

from .tasks import send_order_confirmation_email
from .services import create_order_from_cart

from orders.models import Order  # Django ORM
from .serializers import OrderSerializer

logger = logging.getLogger(__name__)


class OrderViewSet(viewsets.ViewSet):
    """
    Order endpoints (list, retrieve, create) using Django ORM.
    Cart is always read from MongoDB via MongoEngine.
    """

    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def list(self, request, *args, **kwargs):
        """List all orders for current user."""
        orders = Order.objects.filter(user=request.user).order_by("-created_at")
        serializer = OrderSerializer(orders, many=True)
        return Response(serializer.data)

    def retrieve(self, request, pk=None, *args, **kwargs):
        """Get a specific order by ID (must belong to user)."""
        order = get_object_or_404(Order, pk=pk, user=request.user)
        serializer = OrderSerializer(order)
        return Response(serializer.data)

    def create(self, request, *args, **kwargs):
        """Checkout: Create an order from user's cart."""
        try:
            order = create_order_from_cart(request.user, request.data)
        except ValueError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)

        serializer = OrderSerializer(order)
        send_order_confirmation_email.delay(order.id, request.user.email)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["post"], url_path="cancel")
    def cancel(self, request, pk=None, *args, **kwargs):
        """Cancel an order and restore reserved inventory."""
        order = get_object_or_404(Order, pk=pk, user=request.user)
        if order.status not in {Order.Status.PENDING, Order.Status.PROCESSING}:
            return Response(
                {"detail": "Only pending or processing orders can be canceled."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        order.status = Order.Status.CANCELED
        order.save()
        serializer = OrderSerializer(order)
        return Response(serializer.data)
