"""
WSGI config for backend project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/4.2/howto/deployment/wsgi/
"""

import os

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "backend.settings")

from . import datadog  # noqa: F401,E402
from . import opentelemetry  # noqa: F401,E402
from django.core.wsgi import get_wsgi_application  # noqa: E402

application = get_wsgi_application()
