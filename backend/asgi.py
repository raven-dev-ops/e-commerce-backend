"""
ASGI config for backend project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/4.2/howto/deployment/asgi/
"""

import os
from importlib import util

# Enable DataDog APM if available
if util.find_spec("ddtrace"):  # pragma: no cover - optional dependency
    from ddtrace import patch_all  # type: ignore

    patch_all(mongoengine=False)

from django.core.asgi import get_asgi_application
from channels.auth import AuthMiddlewareStack
from channels.routing import ProtocolTypeRouter, URLRouter

import orders.routing

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "backend.settings")

django_asgi_app = get_asgi_application()

application = ProtocolTypeRouter(
    {
        "http": django_asgi_app,
        "websocket": AuthMiddlewareStack(
            URLRouter(orders.routing.websocket_urlpatterns)
        ),
    }
)
