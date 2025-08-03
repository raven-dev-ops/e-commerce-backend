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
