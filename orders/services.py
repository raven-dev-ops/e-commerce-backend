"""Service layer for order-related operations."""

from __future__ import annotations

from io import BytesIO
import logging
from typing import Any

import stripe
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from django.conf import settings
from django.utils import timezone

from authentication.models import Address
from orders.models import Order, OrderItem

from backend.currency import get_exchange_rate


logger = logging.getLogger(__name__)


def create_order_from_cart(user, data) -> Order:
    """
    Legacy server-side cart backed checkout has been removed.

    The frontend is now responsible for cart + pricing. If you need a
    server-side checkout again, implement a new flow that takes a
    fully-priced order payload from the client instead of reading from a
    server-side cart store.
    """

    raise ValueError("Server-side cart checkout is disabled.")


def release_reserved_inventory(order: Order) -> None:
    """
    No-op now that inventory is no longer tracked on the backend.

    Left in place so existing call sites don't fail, but it performs
    no database operations.
    """

    return None


def generate_invoice_pdf(order: Order) -> bytes:
    """Generate a simple PDF invoice for the given order."""

    buffer = BytesIO()
    p = canvas.Canvas(buffer, pagesize=letter)
    y = 750
    p.setFont("Helvetica", 12)
    p.drawString(50, y, f"Invoice for Order #{order.id}")
    y -= 25
    p.drawString(50, y, f"Customer: {order.user.username}")
    y -= 40
    p.drawString(50, y, "Items:")
    y -= 20
    for item in order.items.all():
        p.drawString(
            60,
            y,
            f"{item.product_name} (x{item.quantity}) - ${item.unit_price}",
        )
        y -= 20
    y -= 20
    p.drawString(50, y, f"Total: ${order.total_price}")
    p.showPage()
    p.save()
    pdf = buffer.getvalue()
    buffer.close()
    return pdf
