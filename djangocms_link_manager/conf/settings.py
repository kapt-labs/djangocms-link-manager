from django.conf import settings

def default_handler(plugin):
    """
    Must return a dict `{title: "The page title", "url": "http://page-url/"}`
    or `None` if no data has been found (the plugin is orphaned)
    """
    return

PLACEHOLDER_OUTSIDE_CMS_HANDLER = getattr(settings, "LINK_MANAGER_PLACEHOLDER_OUTSIDE_CMS_HANDLER", default_handler)

MAX_REDIRECT = getattr(settings, "LINK_MANAGER_MAX_REDIRECT", 3)