"""Signal handlers for the users app."""

from django.contrib.auth import get_user_model
from django.contrib.sessions.models import Session
from django.db.models.signals import pre_save
from django.dispatch import receiver


User = get_user_model()


@receiver(pre_save, sender=User)
def revoke_sessions_on_password_change(sender, instance, **kwargs):
    """Delete user sessions if the password has changed."""
    if not instance.pk:
        return

    try:
        old_password = sender.objects.get(pk=instance.pk).password
    except sender.DoesNotExist:  # pragma: no cover - safety check
        return

    if old_password != instance.password:
        for session in Session.objects.all():
            data = session.get_decoded()
            if data.get("_auth_user_id") == str(instance.pk):
                session.delete()
