import os
from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "backend.settings")

app = Celery("backend")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()

# Import monitoring signals for metrics and failure alerts
import backend.celery_monitoring  # noqa: E402,F401

__all__ = ("app",)
