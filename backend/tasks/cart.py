from datetime import datetime, timedelta

from celery import shared_task
from django.conf import settings

from cart.models import Cart, CartItem


@shared_task
def purge_inactive_carts() -> None:
    """Delete carts and items inactive for a configurable number of days."""
    cutoff = datetime.utcnow() - timedelta(
        days=getattr(settings, "CART_INACTIVITY_DAYS", 30)
    )
    inactive_carts = Cart.objects(updated_at__lt=cutoff)
    CartItem.objects(cart__in=inactive_carts).delete()
    inactive_carts.delete()

