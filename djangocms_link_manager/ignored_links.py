from datetime import timedelta
from urllib.parse import urlparse, urlunparse

from django.core.cache import cache
from django.utils.timezone import now

from .conf import settings as local_settings

CACHE_KEY = "djangocms_link_manager:ignored_links"


def clear_ignored_links_cache():
    cache.delete(CACHE_KEY)


def normalize_url_for_ignore(url, scheme=None, netloc=None, absolute_http_only=False):
    """
    Canonical URL key for matching ignore rows to report hrefs.
    Admin rows must be absolute http(s) URLs (absolute_http_only=True).
    During check_links, relative hrefs are resolved with the command scheme and host.
    """
    url = (url or "").strip()
    if not url:
        return None

    parts = urlparse(url)
    if parts.scheme in ("http", "https"):
        pass
    elif absolute_http_only:
        return None
    elif not scheme or not netloc:
        return None
    elif url.startswith("//"):
        parts = urlparse(f"{scheme.lower()}:{url}")
    elif url.startswith("/"):
        parts = urlparse(f"{scheme.lower()}://{netloc}{url}")
    else:
        return None

    if parts.scheme not in ("http", "https") or not parts.netloc:
        return None

    path = parts.path or "/"
    if path != "/" and path.endswith("/"):
        path = path.rstrip("/")

    host = parts.netloc.lower()
    if host.endswith(":80") and parts.scheme.lower() == "http":
        host = host[:-3]
    if host.endswith(":443") and parts.scheme.lower() == "https":
        host = host[:-4]

    return urlunparse((parts.scheme.lower(), host, path, "", parts.query, ""))


def get_active_ignored_links():
    cached = cache.get(CACHE_KEY)
    if cached is not None:
        return cached

    from .models import LinkCheckIgnoredLink

    entries = {
        row["normalized_url"]: {"since": row["created"], "comment": row["comment"]}
        for row in LinkCheckIgnoredLink.objects.filter(active=True).values(
            "normalized_url", "created", "comment"
        )
    }
    cache.set(CACHE_KEY, entries, 300)
    return entries


def link_manual_ignore_info(url, scheme, netloc):
    """Return ignore metadata when a broken href matches an active ignore row."""
    if not url:
        return None

    key = normalize_url_for_ignore(url, scheme=scheme, netloc=netloc)
    if not key:
        return None

    entry = get_active_ignored_links().get(key)
    if not entry:
        return None

    stale = (now() - entry["since"]) >= timedelta(days=local_settings.IGNORE_STALE_DAYS)
    return {"since": entry["since"], "comment": entry["comment"], "stale": stale}
