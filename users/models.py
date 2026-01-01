# users/models.py

from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError
from django.core.validators import FileExtensionValidator
from django.db import models
from django.db.models.functions import Lower
import uuid


def validate_avatar_size(image):
    max_size = 2 * 1024 * 1024  # 2MB
    if image.size > max_size:
        raise ValidationError("Avatar file size must be under 2MB.")


class User(AbstractUser):
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    email_verified = models.BooleanField(default=False)
    verification_token = models.UUIDField(
        default=uuid.uuid4, null=True, blank=True, db_index=True
    )
    avatar = models.ImageField(
        upload_to="avatars/",
        null=True,
        blank=True,
        validators=[
            FileExtensionValidator(["jpg", "jpeg", "png"]),
            validate_avatar_size,
        ],
    )
    mfa_secret = models.CharField(max_length=32, blank=True, null=True)
    is_paused = models.BooleanField(default=False)
    marketing_opt_in = models.BooleanField(default=False)
    marketing_opt_in_at = models.DateTimeField(null=True, blank=True)
    marketing_opt_out_at = models.DateTimeField(null=True, blank=True)

    def save(self, *args, **kwargs):
        if self.email:
            self.email = self.email.strip().lower()
        return super().save(*args, **kwargs)

    class Meta(AbstractUser.Meta):
        constraints = [
            models.UniqueConstraint(
                Lower("email"),
                name="unique_user_email_ci",
                condition=~models.Q(email=""),
            )
        ]

    def __str__(self):
        return self.username
