# orders/models.py

from django.db import models
from django.conf import settings
from authentication.models import Address  # Adjust import if Address is elsewhere


class Order(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "Pending Payment"
        PROCESSING = "processing", "Processing"
        SHIPPED = "shipped", "Shipped"
        DELIVERED = "delivered", "Delivered"
        CANCELED = "canceled", "Canceled"
        FAILED = "failed", "Payment Failed"

    STATUS_CHOICES = Status.choices

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="orders"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    shipping_cost = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    tax_amount = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    payment_intent_id = models.CharField(max_length=255, blank=True, null=True)
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default=Status.PENDING
    )
    shipping_address = models.ForeignKey(
        Address,
        related_name="shipping_orders",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
    )
    billing_address = models.ForeignKey(
        Address,
        related_name="billing_orders",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
    )
    discount_code = models.CharField(max_length=50, blank=True, null=True)
    shipped_date = models.DateTimeField(null=True, blank=True)
    discount_type = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        choices=[("percentage", "Percentage"), ("fixed", "Fixed")],
    )
    discount_value = models.FloatField(blank=True, null=True)
    discount_amount = models.FloatField(blank=True, null=True)

    def __str__(self):
        return f"Order #{self.id} by {self.user.username}"

    def save(self, *args, **kwargs):  # pragma: no cover - exercised via tests
        release = False
        if self.pk:
            previous = Order.objects.get(pk=self.pk)
            if previous.status not in {Order.Status.CANCELED, Order.Status.FAILED} and self.status in {
                Order.Status.CANCELED,
                Order.Status.FAILED,
            }:
                release = True
        super().save(*args, **kwargs)
        if release:
            from orders.services import release_reserved_inventory

            release_reserved_inventory(self)


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items")
    product_name = models.CharField(
        max_length=255
    )  # Or ForeignKey to a Product model if using Django ORM
    quantity = models.PositiveIntegerField()
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.product_name} (x{self.quantity})"
