=======================
django CMS Link Manager
=======================

An extensible means of checking for broken links in virtually any
django CMS plugin.

--------
Overview
--------

There are numerous plugins that provide hyperlink capabilities in django CMS
each with their own fields for store a variety of types of hyperlinks. As a
result, it can become a challenge to find bad links across the whole project.
This project attempts to provide a solution in an extensible manner.

------------
Installation
------------

This package requires Python 3 and Django compatible with your django CMS version.

First, install the package from PyPI: ::

    pip install djangocms-link-manager

Then add it to your ``INSTALLED_APPS``: ::

    # settings.py
    ...
    INSTALLED_APPS = [
        ...
        'djangocms_link_manager',
    ]

Run migrations after upgrading (ignored-link admin storage): ::

    python manage.py migrate djangocms_link_manager

-----
Usage
-----

The simplest way to run this is: ::

    python manage.py check_links

However, this command accepts a number of optional arguments: ::

    --verify-exists     Check that each link's target exists (use caution,
                        makes HTTP HEAD requests).
    --scheme SCHEME     Default scheme to use for scheme-less URLs
                        (default: "http").
    --host NETLOC       Default [host:port] to use for relative URLs (defaults
                        to "localhost:8000").
    --template TEMPLATE Override the report rendering template.
    --mail-managers     Instead of printing report to the console, email it to
                        the addresses defined in the MANAGERS list in the
                        project's settings.py.
    --only-page-with-reverse-id ONLY_PAGE_REVERSE_ID
                        Check only the page with a given reverse id
    --only-page-with-id ONLY_PAGE_ID
                        Check only the page with a given id
    --only-placeholder-id ONLY_PLACEHOLDER_ID
                        Check only the placeholder with a given id

With ``--verify-exists``, the command prefetches unique http(s) URLs grouped by
host (shared ``requests`` session and per-run result cache). Redirects are
followed up to ``LINK_MANAGER_MAX_REDIRECT`` (default: 3).

Ignored URLs (admin)
--------------------

Known false positives can be stored in **Ignored links (link check)** in the
Django admin (model ``LinkCheckIgnoredLink``). Matching URLs are omitted from
the broken-link list. Entries older than ``LINK_MANAGER_IGNORE_STALE_DAYS``
(default: 365) still appear in a separate **Manually ignored links to review**
section so they can be checked again.

Use an absolute URL starting with ``http://`` or ``https://`` (same target as in
the content). URLs are normalized on save for matching during the report; relative
href in the CMS are still resolved at check time using the check host and scheme.

Configuration
-------------

Optional settings in the project ``settings.py``:

``LINK_MANAGER_REPORT_LANGUAGE``
    Language code for report strings (``{% trans %}`` in the text template).
    Defaults to the project ``LANGUAGE_CODE``.

``LINK_MANAGER_STATIC_EXCLUDED_DOMAINS``
    Hostnames (or subdomains) for which ``--verify-exists`` skips HTTP checks
    (useful when bots are blocked). Example: ``("domain-that-blocks-bots.ext", "another-domain.ext",)``.

``LINK_MANAGER_IGNORE_STALE_DAYS``
    Days after which an admin ignore is listed in the stale review section
    (default: 365).

``LINK_MANAGER_HTTP_CONNECT_TIMEOUT`` / ``LINK_MANAGER_HTTP_READ_TIMEOUT``
    Timeouts in seconds for remote checks when ``--verify-exists`` is enabled
    (defaults: 5 and 10).

``LINK_MANAGER_MAX_REDIRECT``
    Maximum redirects followed during existence checks (default: 3).

``LINK_MANAGER_PLACEHOLDER_OUTSIDE_CMS_HANDLER``
    Callable returning page title and URL for plugins outside CMS pages (see
    existing projects using placeholder fields).

Built-in link managers
----------------------

``LinkPlugin`` and ``Bootstrap3ButtonCMSPlugin`` skip ``mailto``, ``tel`` and
in-page anchors in the report and only run existence checks on http(s) and
site-relative paths for external URLs.


---------
Extending
---------

This package currently supports to plugins by their class names:
``Bootstrap3ButtonCMSPlugin`` and ``LinkPlugin`` which come from the packages:
``aldryn_bootstrap3`` and ``djangocms_link`` respectively. To add support for
a new CMSPlugin, one simply writes creates a class that subclasses
``djangocms_link_manager.link_manager.LinkManager`` and overrides the
``check_link()`` method according to the particulars of the CMSPlugin you wish
to support.

Once this is created, register the link manager into the link manager pool on
startup with: ::

    from djangocms_link_manager.link_manager import LinkManager, LinkReport
    from djangocms_link_manager.link_manager_pool import link_manager_pool

    class MyLinkPluginLinkManager(LinkManager):
        """MyLinkPlugin only contains the fields 'name' and 'url'."""

        def check_link(self, instance, verify_exists=False):
            """Override this method and adapt to MyLinkPlugin."""
            return LinkReport(
                valid=self.validate_url(instance.url, verify_exists=verify_exists),
                text=instance.name,
                url=instance.url
            )

    link_manager_pool.register('MyLinkPlugin', MyLinkPluginLinkManager)


Support for additional URL schemes
----------------------------------

This package already provides support for the following URL schemes: ``ftp``,
``ftps``, ``http``, ``https``, ``bitcoin``, ``mailto``, and ``tel``. If a project
requires validation of other schemes, they can be added to the link manager
(subclass of LinkManager) simply by including a method with the name
``validate_MYSCHEME`` with the signature: ::

    def validate_MYSCHEME(self, parts, verify_exists=False):
        # Do your thing here
        if valid:
            return True
        else:
            return False

Replace "MYSCHEME" with the lower-case scheme of your choice.

``verify_exists``, when set to True, is intended to check to see if the resource
is really available. For example, for ``http(s)``, ``ftp(s)`` validator will
actually attempt to fetch the URL (using an HTTP HEAD request) and will return
``False`` if the result is an HTTP 404 error. Use this responsibly.

``parts`` is a dict of the URLs parts as follows: ::

    parts = {
        'scheme': ...,
        'netloc': ...,
        'path': ...,
        'params': ...,
        'query': ...,
        'fragment': ...,
    }

For more information about these elements, please review the docs for
`urllib.parse <https://docs.python.org/3/library/urllib.html>`_.

Add in a CMS toolbar
--------------------

Add `cms_toolbars.py` file in your project, containing::

    from cms.toolbar_base import CMSToolbar
    from cms.toolbar_pool import toolbar_pool
    from django.core.urlresolvers import reverse
    from django.utils.translation import ugettext_lazy as _

    @toolbar_pool.register
    class SettingsToolbar(CMSToolbar):
        def populate(self):
            link_manager_url = reverse('link-manager:start')
            current_page = self.request.current_page
            if current_page is not None:
                link_manager_url += "?page_id={}".format(current_page.id)

            self.toolbar.add_modal_item(_('Broken link analysis'), url=link_manager_url, on_close=None)