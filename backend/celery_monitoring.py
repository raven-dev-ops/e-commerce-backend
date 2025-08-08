import logging
import time
from typing import Dict

from celery import signals
from prometheus_client import Counter, Histogram
from sentry_sdk import capture_exception

logger = logging.getLogger(__name__)

# Metrics for monitoring Celery tasks
TASK_DURATION = Histogram(
    "celery_task_duration_seconds",
    "Duration of Celery tasks in seconds",
    ["task_name"],
)
TASK_SUCCESSES = Counter(
    "celery_task_success_total",
    "Total number of successful Celery tasks",
    ["task_name"],
)
TASK_FAILURES = Counter(
    "celery_task_failure_total",
    "Total number of failed Celery tasks",
    ["task_name"],
)

_task_start_times: Dict[str, float] = {}


@signals.task_prerun.connect
def task_prerun_handler(sender=None, task_id: str = "", **kwargs) -> None:
    """Record task start time."""
    _task_start_times[task_id] = time.time()


@signals.task_postrun.connect
def task_postrun_handler(
    sender=None, task_id: str = "", state: str | None = None, **kwargs
) -> None:
    """Update metrics after task completion."""
    start = _task_start_times.pop(task_id, None)
    if start is not None:
        duration = time.time() - start
        TASK_DURATION.labels(task_name=sender.name).observe(duration)
    if state == "SUCCESS":
        TASK_SUCCESSES.labels(task_name=sender.name).inc()


@signals.task_failure.connect
def task_failure_handler(
    sender=None, task_id: str = "", exception: Exception | None = None, **kwargs
) -> None:
    """Record task failure metrics and send alert."""
    TASK_FAILURES.labels(task_name=sender.name).inc()
    logger.error("Task %s failed: %s", sender.name, exception)
    if exception is not None:
        capture_exception(exception)
