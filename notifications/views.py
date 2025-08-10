from collections.abc import Iterator
from typing import Optional
import time

from django.http import StreamingHttpResponse

from .models import Notification


def _event_stream(last_id: Optional[int]) -> Iterator[str]:
    """Yield server-sent events for notifications after ``last_id``."""

    current_id = last_id or 0
    while True:
        for notification in Notification.objects.filter(id__gt=current_id).order_by(
            "id"
        ):
            current_id = notification.id
            yield f"id: {current_id}\n"
            yield f"data: {notification.message}\n\n"
        time.sleep(1)


def notifications_stream(request):
    """Stream notifications to the client using Server-Sent Events."""

    last_id_param = request.GET.get("last_id")
    try:
        last_id: Optional[int] = int(last_id_param) if last_id_param else None
    except ValueError:
        last_id = None

    response = StreamingHttpResponse(
        _event_stream(last_id), content_type="text/event-stream"
    )
    response["Cache-Control"] = "no-cache"
    return response
