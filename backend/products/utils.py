# products/utils.py

from django.core.mail import send_mail
from django.conf import settings

def send_low_stock_notification(product_name, product_id, current_stock):
    """
    Sends an email notification to administrators about low stock levels.
    """
    subject = f'Low Stock Alert: {product_name}'
    # Enhance the email message to include more details
    message = (
        f'The following product is running low on stock and requires your attention:\n\n'
        f'Product Name: {product_name}\n'
        f'Current Stock: {current_stock}\n\n'
        f'Please restock this product as soon as possible.'
    )
    from_email = settings.DEFAULT_FROM_EMAIL
    recipient_list = [settings.ADMIN_EMAIL] # Make sure ADMIN_EMAIL is set in your settings.py

    try:
        send_mail(subject, message, from_email, recipient_list)
        print(f"Low stock notification email sent for product: {product_name}") # Optional: for logging success
    except Exception as e:
        print(f"Error sending low stock notification email for product {product_name}: {e}") # Optional: log the error