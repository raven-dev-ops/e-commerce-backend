from django.conf import settings
from django.db import models
from django.utils.crypto import get_random_string


class ReferralCode(models.Model):
    code = models.CharField(max_length=32, unique=True, blank=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    usage_count = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if not self.code:
            self.code = get_random_string(10).upper()
        super().save(*args, **kwargs)

    def __str__(self) -> str:
        return self.code
