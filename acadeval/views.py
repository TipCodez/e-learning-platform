from pathlib import PurePosixPath

from django.conf import settings
from django.http import Http404
from django.views.static import serve


def public_media(request, path):
    normalized = PurePosixPath(path).as_posix().lstrip("/")
    allowed_prefixes = getattr(settings, "PUBLIC_MEDIA_PREFIXES", ())
    if ".." in PurePosixPath(normalized).parts:
        raise Http404("Media not found")
    if not any(normalized.startswith(prefix) for prefix in allowed_prefixes):
        raise Http404("Media not found")
    return serve(request, normalized, document_root=settings.MEDIA_ROOT)
