from django.conf import settings
from django.db import models
from django.utils.crypto import get_random_string


class GiftCard(models.Model):
    code = models.CharField(max_length=32, unique=True, blank=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    balance = models.DecimalField(max_digits=10, decimal_places=2, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    redeemed_at = models.DateTimeField(null=True, blank=True)
    redeemed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL
    )

    def save(self, *args, **kwargs):
        if not self.code:
            self.code = get_random_string(16).upper()
        if self.balance is None:
            self.balance = self.amount
        super().save(*args, **kwargs)
