import socket
import time
from collections import OrderedDict
from urllib.parse import urljoin, urlparse, urlunparse

import requests
from requests.adapters import HTTPAdapter

from .conf import settings as local_settings
from .ignored_links import normalize_url_for_ignore

USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:83.0) "
    "Gecko/20100101 Firefox/83.0"
)

_active_context = None


def get_active_http_context():
    return _active_context


def set_active_http_context(context):
    global _active_context
    _active_context = context


def host_skips_http_check(url):
    """True when LINK_MANAGER_STATIC_EXCLUDED_DOMAINS matches the URL host."""
    host = (urlparse(url).netloc or "").split(":")[0].lower().strip(".")
    if not host:
        return False
    for raw in local_settings.STATIC_EXCLUDED_DOMAINS:
        domain = raw.strip().lower()
        if domain.startswith("http://") or domain.startswith("https://"):
            domain = domain.split("://", 1)[1].split("/")[0]
        domain = domain.split(":")[0].strip(".")
        if not domain:
            continue
        if host == domain or host.endswith(f".{domain}"):
            return True
    return False


def absolute_url_for_check(manager, url):
    parts = OrderedDict(
        zip(
            ["scheme", "netloc", "path", "params", "query", "fragment"],
            urlparse(url),
        )
    )
    if not parts["scheme"]:
        parts["scheme"] = manager.scheme
    if not parts["netloc"]:
        parts["netloc"] = manager.netloc
    return urlunparse(parts.values())


def cache_key_for_url(manager, url):
    absolute = absolute_url_for_check(manager, url)
    return normalize_url_for_ignore(
        absolute, scheme=manager.scheme, netloc=manager.netloc
    ) or absolute


class LinkCheckHttpContext:
    """Shared session and per-run URL cache for check_links --verify-exists."""

    def __init__(self, scheme, netloc):
        self.scheme = scheme
        self.netloc = netloc
        self._cache = {}
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": USER_AGENT})
        adapter = HTTPAdapter(pool_connections=16, pool_maxsize=16)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)
        self.timeout = (
            local_settings.HTTP_CONNECT_TIMEOUT,
            local_settings.HTTP_READ_TIMEOUT,
        )

    def close(self):
        self.session.close()

    def verify(self, manager, url, redirection_count=0):
        absolute = absolute_url_for_check(manager, url)
        key = cache_key_for_url(manager, url)
        if key in self._cache:
            return self._cache[key]
        if host_skips_http_check(absolute):
            self._cache[key] = True
            return True
        result = self._fetch(absolute, redirection_count)
        self._cache[key] = result
        return result

    def prefetch_urls(self, manager, urls):
        unique = set(urls)

        def sort_key(u):
            absolute = absolute_url_for_check(manager, u)
            return (urlparse(absolute).netloc.lower(), cache_key_for_url(manager, u))

        for url in sorted(unique, key=sort_key):
            self.verify(manager, url)

    def _fetch(self, url, redirection_count):
        try:
            response = self.session.head(
                url, allow_redirects=False, timeout=self.timeout
            )
            if 400 <= response.status_code <= 500:
                raise requests.HTTPError(response=response)
            if response.status_code in (301, 302, 303, 307, 308):
                redirection_count += 1
                if redirection_count >= local_settings.MAX_REDIRECT:
                    return False
                location = response.headers.get("Location")
                if not location:
                    return False
                return self._fetch(urljoin(url, location), redirection_count)
            return 200 <= response.status_code < 400
        except requests.HTTPError:
            try:
                time.sleep(0.25)
                response = self.session.get(
                    url, allow_redirects=False, timeout=self.timeout
                )
                if response.status_code in (301, 302, 303, 307, 308):
                    redirection_count += 1
                    if redirection_count >= local_settings.MAX_REDIRECT:
                        return False
                    location = response.headers.get("Location")
                    if not location:
                        return False
                    return self._fetch(urljoin(url, location), redirection_count)
                return 200 <= response.status_code < 400
            except (
                requests.HTTPError,
                requests.ConnectionError,
                requests.Timeout,
                requests.TooManyRedirects,
                UnicodeEncodeError,
                socket.error,
            ):
                return False
        except (
            requests.ConnectionError,
            requests.Timeout,
            requests.TooManyRedirects,
            UnicodeEncodeError,
            socket.error,
        ):
            return False


def collect_prefetch_urls(link_plugins, get_manager, scheme, netloc):
    stub = get_manager("LinkPlugin", scheme, netloc)
    urls = set()
    for link_plugin in link_plugins.iterator():
        plugin_inst, _ = link_plugin.get_plugin_instance()
        if not plugin_inst:
            continue
        manager = get_manager(plugin_inst.plugin_type, scheme, netloc)
        if not manager:
            continue
        link_reports = manager.check_link(plugin_inst, verify_exists=False)
        if not isinstance(link_reports, list):
            link_reports = [link_reports]
        for link_report in link_reports:
            if not link_report.valid or not isinstance(link_report.url, str):
                continue
            url = link_report.url.strip()
            if not url:
                continue
            absolute = absolute_url_for_check(stub, url)
            parts = urlparse(absolute)
            if parts.scheme not in ("http", "https"):
                continue
            if host_skips_http_check(absolute):
                continue
            urls.add(url)
    return urls
