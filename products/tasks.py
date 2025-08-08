from celery import shared_task
from django.core.mail import send_mail
from django.conf import settings
import boto3
from io import BytesIO
from products.models import Product


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


@shared_task
def upload_product_image_to_s3(product_id: str, filename: str, content: bytes) -> None:
    """Upload a product image to S3 and update the product record."""
    bucket = settings.AWS_S3_BUCKET
    if not bucket:
        return
    s3 = boto3.client("s3")
    key = f"products/{product_id}/{filename}"
    s3.upload_fileobj(BytesIO(content), bucket, key)
    url = f"https://{bucket}.s3.amazonaws.com/{key}"
    product = Product.objects(_id=product_id).first()
    if product:
        product.images.append(url)
        product.save()
