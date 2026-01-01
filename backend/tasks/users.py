from datetime import timedelta

from celery import shared_task
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.sessions.models import Session
from django.core.mail import send_mail
from django.utils import timezone


@shared_task(
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_backoff_max=3600,
    retry_jitter=True,
    retry_kwargs={"max_retries": 5},
)
def send_verification_email(user_id):
    User = get_user_model()
    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        return
    link = f"{getattr(settings, 'FRONTEND_URL', '')}/authentication/verify-email/{user.verification_token}/"
    subject = "Verify your email"
    message = f"Please verify your email by visiting: {link}"
    from_email = getattr(settings, "DEFAULT_FROM_EMAIL", None)
    send_mail(subject, message, from_email, [user.email])


@shared_task
def cleanup_expired_sessions():
    """Delete expired user sessions."""
    Session.objects.filter(expire_date__lt=timezone.now()).delete()


def perform_user_purge() -> int:
    """Remove inactive users beyond the retention window."""
    User = get_user_model()
    retention = getattr(settings, "PERSONAL_DATA_RETENTION_DAYS", 365)
    cutoff = timezone.now() - timedelta(days=retention)
    qs = User.objects.filter(is_active=False, last_login__lt=cutoff)
    deleted, _ = qs.delete()
    return deleted


@shared_task
def purge_inactive_users() -> None:
    """Celery task wrapper for inactive user purge."""
    perform_user_purge()

