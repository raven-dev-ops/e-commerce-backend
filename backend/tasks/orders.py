from celery import shared_task
from datetime import timedelta
import logging
from django.conf import settings
from django.core.mail import send_mail
from django.db import transaction
from django.utils import timezone
from orders.models import Order

logger = logging.getLogger(__name__)


@shared_task
def send_order_confirmation_email(order_id, user_email):
    """Send order confirmation email to the user."""
    subject = f"Order Confirmation #{order_id}"
    message = f"Thank you for your order. Your order ID is {order_id}."
    from_email = getattr(settings, "DEFAULT_FROM_EMAIL", None)
    send_mail(subject, message, from_email, [user_email])


@shared_task
def send_order_status_sms(order_id, status, to_phone):
    """Send SMS notification for order status updates."""
    account_sid = getattr(settings, "TWILIO_ACCOUNT_SID", "")
    auth_token = getattr(settings, "TWILIO_AUTH_TOKEN", "")
    from_number = getattr(settings, "TWILIO_FROM_NUMBER", "")
    if not all([account_sid, auth_token, from_number, to_phone]):
        return
    from twilio.rest import Client

    client = Client(account_sid, auth_token)
    message = f"Your order #{order_id} status is now {status}."
    client.messages.create(body=message, from_=from_number, to=to_phone)

@shared_task
def auto_cancel_stale_pending_orders() -> int:
    from orders.services import transition_order_status

    timeout_minutes = int(getattr(settings, "ORDER_PENDING_TIMEOUT_MINUTES", 30))
    if timeout_minutes <= 0:
        return 0

    cutoff = timezone.now() - timedelta(minutes=timeout_minutes)
    stale_ids = list(
        Order.objects.filter(
            status=Order.Status.PENDING,
            created_at__lt=cutoff,
        ).values_list("id", flat=True)
    )

    canceled = 0
    for order_id in stale_ids:
        with transaction.atomic():
            order = (
                Order.objects.select_for_update()
                .select_related("user")
                .prefetch_related("items")
                .filter(id=order_id)
                .first()
            )
            if not order or order.status != Order.Status.PENDING:
                continue
            transition_order_status(order, Order.Status.CANCELED)
            canceled += 1

    if canceled:
        logger.info("Auto-canceled %s stale pending orders.", canceled)
    return canceled

