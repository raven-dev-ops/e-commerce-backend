"""
ASGI config for backend project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/4.2/howto/deployment/asgi/
"""

import os

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "backend.settings")

from . import datadog  # noqa: F401,E402
from . import opentelemetry  # noqa: F401,E402

from django.core.asgi import get_asgi_application  # noqa: E402
from channels.auth import AuthMiddlewareStack  # noqa: E402
from channels.routing import ProtocolTypeRouter, URLRouter  # noqa: E402

import orders.routing  # noqa: E402

django_asgi_app = get_asgi_application()

application = ProtocolTypeRouter(
    {
        "http": django_asgi_app,
        "websocket": AuthMiddlewareStack(
            URLRouter(orders.routing.websocket_urlpatterns)
        ),
    }
)
