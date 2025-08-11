import os

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "backend.settings")

from . import datadog  # noqa: F401,E402
from . import opentelemetry  # noqa: F401,E402

from celery import Celery  # noqa: E402

app = Celery("backend")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()

# Import monitoring signals for metrics and failure alerts
import backend.celery_monitoring  # noqa: E402,F401

__all__ = ("app",)
