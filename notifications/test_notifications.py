import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "backend.settings")
django.setup()

from django.contrib.auth import get_user_model  # noqa: E402
from django.test import RequestFactory, TestCase  # noqa: E402

from .models import Notification  # noqa: E402
from .views import _event_stream, notifications_stream  # noqa: E402


class NotificationStreamTests(TestCase):
    def setUp(self) -> None:
        self.user = get_user_model().objects.create_user(
            username="user", email="user@example.com", password="pass1234"
        )

    def test_event_stream_yields_notifications(self) -> None:
        Notification.objects.create(user=self.user, message="hello")
        generator = _event_stream(None)
        self.assertIn("id:", next(generator))
        self.assertEqual(next(generator), "data: hello\n\n")

    def test_notifications_stream_view(self) -> None:
        Notification.objects.create(user=self.user, message="ping")
        request = RequestFactory().get("/notifications/stream/")
        response = notifications_stream(request)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "text/event-stream")
        stream = response.streaming_content
        # Consume id and data lines
        next(stream)
        self.assertEqual(next(stream).decode(), "data: ping\n\n")
