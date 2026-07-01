"""ASGI config for Acadeval."""
import os

from django.core.asgi import get_asgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "acadeval.settings")

application = get_asgi_application()
