# orders/views.py

from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import (
    action,
    api_view,
    authentication_classes,
    permission_classes,
)
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.shortcuts import get_object_or_404
from django.http import HttpResponse
import logging
from django.conf import settings
from django.utils.dateparse import parse_datetime

from .tasks import send_order_confirmation_email
from .services import create_order_from_cart, generate_invoice_pdf

from orders.models import Order  # Django ORM
from backend.serializers.orders import OrderSerializer

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
        orders = (
            Order.objects.filter(user=request.user)
            .select_related("shipping_address", "billing_address")
            .prefetch_related("items")
            .order_by("-created_at")
        )
        serializer = OrderSerializer(orders, many=True)
        return Response(serializer.data)

    def retrieve(self, request, pk=None, *args, **kwargs):
        """Get a specific order by ID (must belong to user)."""
        order = get_object_or_404(
            Order.objects.select_related(
                "shipping_address", "billing_address"
            ).prefetch_related("items"),
            pk=pk,
            user=request.user,
        )
        serializer = OrderSerializer(order)
        return Response(serializer.data)

    @action(detail=True, methods=["get"], url_path="invoice")
    def invoice(self, request, pk=None, *args, **kwargs):
        """Download the invoice for the order as a PDF."""

        order = get_object_or_404(
            Order.objects.prefetch_related("items"), pk=pk, user=request.user
        )
        pdf_bytes = generate_invoice_pdf(order)
        response = HttpResponse(pdf_bytes, content_type="application/pdf")
        response["Content-Disposition"] = (
            f'attachment; filename="invoice_{order.id}.pdf"'
        )
        return response

    def create(self, request, *args, **kwargs):
        """Checkout: Create an order from user's cart."""
        try:
            order = create_order_from_cart(request.user, request.data)
        except ValueError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)

        order = (
            Order.objects.select_related("shipping_address", "billing_address")
            .prefetch_related("items")
            .get(pk=order.pk)
        )
        serializer = OrderSerializer(order)
        send_order_confirmation_email.delay(order.id, request.user.email)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["post"], url_path="cancel")
    def cancel(self, request, pk=None, *args, **kwargs):
        """Cancel an order and restore reserved inventory."""
        order = get_object_or_404(
            Order.objects.select_related(
                "shipping_address", "billing_address"
            ).prefetch_related("items"),
            pk=pk,
            user=request.user,
        )
        if order.status not in {Order.Status.PENDING, Order.Status.PROCESSING}:
            return Response(
                {"detail": "Only pending or processing orders can be canceled."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        order.status = Order.Status.CANCELED
        order.save()
        serializer = OrderSerializer(order)
        return Response(serializer.data)


@api_view(["POST"])
@authentication_classes([])
@permission_classes([AllowAny])
def shipment_tracking_webhook(request, version):
    """Receive shipment tracking updates from external carriers."""
    secret = request.headers.get("X-Webhook-Token", "")
    expected = getattr(settings, "SHIPMENT_WEBHOOK_SECRET", "")
    if expected and secret != expected:
        return Response(
            {"detail": "Invalid token."}, status=status.HTTP_401_UNAUTHORIZED
        )

    order_id = request.data.get("order_id")
    status_value = request.data.get("status")
    if not order_id or not status_value:
        return Response(
            {"detail": "order_id and status are required."},
            status=status.HTTP_400_BAD_REQUEST,
        )
    try:
        order = Order.all_objects.get(pk=order_id)
    except Order.DoesNotExist:
        return Response(
            {"detail": "Order not found."}, status=status.HTTP_404_NOT_FOUND
        )

    valid_statuses = {choice[0] for choice in Order.STATUS_CHOICES}
    if status_value not in valid_statuses:
        return Response(
            {"detail": "Invalid status."}, status=status.HTTP_400_BAD_REQUEST
        )

    shipped_date = request.data.get("shipped_date")
    update_fields = ["status"]
    order.status = status_value
    if shipped_date:
        parsed = parse_datetime(shipped_date)
        if parsed:
            order.shipped_date = parsed
            update_fields.append("shipped_date")
    order.save(update_fields=update_fields)
    return Response({"detail": "Shipment update received."})
