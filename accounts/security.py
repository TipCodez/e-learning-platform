import hashlib

from django.core.cache import cache


def _client_ip(request):
    forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR", "")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR", "unknown")


def _cache_key(scope, request, identifier=""):
    identity = f"{_client_ip(request)}:{identifier}".lower().encode("utf-8")
    digest = hashlib.sha256(identity).hexdigest()
    return f"acadeval:throttle:{scope}:{digest}"


def throttle_hit(scope, request, *, identifier="", limit=10, window=600):
    key = _cache_key(scope, request, identifier)
    added = cache.add(key, 1, timeout=window)
    if added:
        return False
    try:
        attempts = cache.incr(key)
    except ValueError:
        cache.set(key, 1, timeout=window)
        return False
    return attempts > limit


def throttle_is_blocked(scope, request, *, identifier="", limit=10):
    attempts = cache.get(_cache_key(scope, request, identifier), 0)
    return attempts >= limit


def throttle_clear(scope, request, *, identifier=""):
    cache.delete(_cache_key(scope, request, identifier))
