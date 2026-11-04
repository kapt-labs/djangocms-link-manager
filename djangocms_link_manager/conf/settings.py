from django.conf import settings

def default_handler(plugin):
    """
    Must return a dict `{title: "The page title", "url": "http://page-url/"}`
    or `None` if no data has been found (the plugin is orphaned)
    """
    return

PLACEHOLDER_OUTSIDE_CMS_HANDLER = getattr(settings, "LINK_MANAGER_PLACEHOLDER_OUTSIDE_CMS_HANDLER", default_handler)

MAX_REDIRECT = getattr(settings, "LINK_MANAGER_MAX_REDIRECT", 3)

STATIC_EXCLUDED_DOMAINS = getattr(settings, "LINK_MANAGER_STATIC_EXCLUDED_DOMAINS", ())

IGNORE_STALE_DAYS = getattr(settings, "LINK_MANAGER_IGNORE_STALE_DAYS", 365)

IGNORE_URL_DEFAULT_SCHEME = getattr(settings, "LINK_MANAGER_IGNORE_URL_DEFAULT_SCHEME", "https")

HTTP_CONNECT_TIMEOUT = getattr(settings, "LINK_MANAGER_HTTP_CONNECT_TIMEOUT", 5)

HTTP_READ_TIMEOUT = getattr(settings, "LINK_MANAGER_HTTP_READ_TIMEOUT", 10)