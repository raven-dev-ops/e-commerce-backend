import os
from importlib import util

# Enable DataDog APM if available
if util.find_spec("ddtrace"):  # pragma: no cover - optional dependency
    from ddtrace import patch_all  # type: ignore

    patch_all(mongoengine=False)

from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "backend.settings")

app = Celery("backend")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()

# Import monitoring signals for metrics and failure alerts
import backend.celery_monitoring  # noqa: E402,F401

__all__ = ("app",)
