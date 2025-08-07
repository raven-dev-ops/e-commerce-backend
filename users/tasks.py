from celery import shared_task
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.sessions.models import Session
from django.core.mail import send_mail
from django.utils import timezone


@shared_task
def send_verification_email(user_id):
    User = get_user_model()
    user = User.objects.get(id=user_id)
    link = f"{getattr(settings, 'FRONTEND_URL', '')}/authentication/verify-email/{user.verification_token}/"
    subject = "Verify your email"
    message = f"Please verify your email by visiting: {link}"
    from_email = getattr(settings, "DEFAULT_FROM_EMAIL", None)
    send_mail(subject, message, from_email, [user.email])


@shared_task
def cleanup_expired_sessions():
    """Delete expired user sessions."""
    Session.objects.filter(expire_date__lt=timezone.now()).delete()
