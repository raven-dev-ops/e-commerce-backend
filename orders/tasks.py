from celery import shared_task
from django.core.mail import send_mail
from django.conf import settings


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
