from celery import shared_task
from django.core.mail import send_mail
from django.conf import settings


@shared_task
def send_low_stock_email(
    product_name: str, product_id: str, current_stock: int
) -> None:
    """Send low stock notification email."""
    subject = f"Low Stock Alert: {product_name}"
    message = (
        f"The following product is running low on stock and requires your attention:\n\n"
        f"Product Name: {product_name}\n"
        f"Current Stock: {current_stock}\n\n"
        f"Please restock this product as soon as possible."
    )
    from_email = settings.DEFAULT_FROM_EMAIL
    recipient_list = [settings.ADMIN_EMAIL]
    send_mail(subject, message, from_email, recipient_list)
