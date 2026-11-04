# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import codecs
import phonenumbers
import requests
import socket
import time
import warnings

from collections import OrderedDict
from hashlib import sha256

from urllib.parse import urlparse, urlunparse

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import EmailValidator
from django.core.validators import URLValidator

import attr
from .conf import settings as local_settings


def hyperlink_should_be_audited(url):
    """HTTP broken-link checks apply to paths and http(s) URLs only."""
    url = (url or "").strip()
    if not url or url.startswith("#"):
        return False
    lower = url.lower()
    if lower.startswith("javascript:"):
        return False
    if lower.startswith("//"):
        return True
    parts = urlparse(url)
    if not parts.scheme:
        return True
    return parts.scheme in ("http", "https")


@attr.s(slots=True)
class LinkReport(object):
    valid = attr.ib()
    text = attr.ib()
    url = attr.ib()


@attr.s(slots=True)
class LinkManager(object):
    """
    Defines an interface for the link manager.
    """

    scheme = attr.ib(default="http")
    netloc = attr.ib(default="localhost:8000")

    def verify_link_exists(self, url, redirection_count=0):
        from .http_check import get_active_http_context, host_skips_http_check

        if host_skips_http_check(url):
            return True

        ctx = get_active_http_context()
        if ctx is not None:
            return ctx.verify(self, url, redirection_count)

        return self._verify_link_exists_without_context(url, redirection_count)

    def _verify_link_exists_without_context(self, url, redirection_count=0):
        """Fallback when check_links has not installed a shared HTTP context."""
        try:
            response = requests.head(
                url,
                timeout=(
                    local_settings.HTTP_CONNECT_TIMEOUT,
                    local_settings.HTTP_READ_TIMEOUT,
                ),
            )
            if (
                400 <= response.status_code <= 500
            ):  # Some sites do not handle HEAD requests correctly
                raise requests.HTTPError
            elif response.status_code in [301, 302]:
                redirection_count += 1
                if redirection_count < local_settings.MAX_REDIRECT:
                    return self._verify_link_exists_without_context(
                        response.next.url, redirection_count
                    )
                else:
                    return False
            else:
                return 200 <= response.status_code < 400  # pragma: no cover

        except requests.HTTPError:
            try:
                time.sleep(0.25)
                response = requests.get(
                    url,
                    headers={
                        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:83.0) Gecko/20100101 Firefox/83.0"
                    },
                    timeout=(
                        local_settings.HTTP_CONNECT_TIMEOUT,
                        local_settings.HTTP_READ_TIMEOUT,
                    ),
                )
                if response.status_code in [301, 302]:
                    redirection_count += 1
                    if redirection_count < local_settings.MAX_REDIRECT:
                        return self._verify_link_exists_without_context(
                            response.next.url, redirection_count
                        )
                    else:
                        return False
                else:
                    return 200 <= response.status_code < 400  # pragma: no cover
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

    def validate_default(self, parts, verify_exists=False):
        """
        Validation for FTP, FTPS, HTTP, and HTTPS scehems.
        When `verify_exists` is set to True, this validator will make HEAD
        requests for the URL and will return False if the URL returns a status
        outside of the range of 200 >= «status» > 400.

        :param parts:
        :param verify_exists:
        :return:
        """
        validator = URLValidator()
        if not parts["netloc"]:
            # If there is no host/port, then this may be a link to a local
            # resource (media or static asset, etc.) Use the provided default.
            parts["netloc"] = self.netloc
        url = urlunparse(parts.values())
        try:
            validator(url)
        except ValidationError:
            return False
        else:
            if verify_exists:
                return self.verify_link_exists(url)
            else:
                return True

    def validate_mailto(self, email, verify_exists=False):
        """
        Validates a mailto URL, by using Django's EmailValidator.
        `verify_exists` does nothing at this time.

        :param parts:
        :param verify_exists:
        :return:
        """
        validator = EmailValidator()
        try:
            validator(email)
        except ValidationError:
            return False
        else:
            return True

    def validate_bitcoin(self, parts, verify_exists=False):
        """
        Checks that the address portion of the URL has a valid checksum.
        `verify_exists` does nothing at this time.

        :param parts:
        :param verify_exists:
        :return:
        """
        # Code borrowed from:
        # https://rosettacode.org/wiki/Bitcoin/address_validation#Python
        digits58 = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"

        def to_bytes(n, length):
            s = "%x" % n
            s = s.rjust(length * 2, "0")
            s = codecs.decode(s.encode("UTF-8"), "hex_codec")
            return s

        def decode_base58(bc, length):
            n = 0
            for char in bc:
                n = n * 58 + digits58.index(char)
            return to_bytes(n, length)

        def check_bc(bc):
            bcbytes = decode_base58(bc, 25)
            return bcbytes[-4:] == sha256(sha256(bcbytes[:-4]).digest()).digest()[:4]

        btc_address = parts["path"]
        return check_bc(btc_address)

    def validate_tel(self, phone_number, verify_exists=False):
        """
        Checks if the number is parsable and is a 'possible number'.
        `verify_exists` doesn't attempt to make a call, but checks that the
        number is also in an assigned exchange.

        :param parts:
        :param verify_exists:
        :return:
        """
        try:
            parsed_num = phonenumbers.parse(
                phone_number, settings.LANGUAGE_CODE.upper()
            )
        except phonenumbers.NumberParseException:
            return False
        else:
            if verify_exists:
                return phonenumbers.is_valid_number(parsed_num)
            else:
                return phonenumbers.is_possible_number(parsed_num)

    def validate_url(self, url, verify_exists=False):
        """
        Utility for checking any URL. This is the primary entry-point. This
        method acts as a router to the various scheme-specific validators.

        :param url:
        :param verify_exists:
        :return:
        """
        if not url:
            # Special case. If an empty string is passed as the URL. Without
            # this test, it becomes a relative link to the root of the
            # project, which it kinda is, but isn't quite right. Also catches
            # `None`, etc.
            return False

        parts = OrderedDict(
            zip(
                ["scheme", "netloc", "path", "params", "query", "fragment"],
                urlparse(url),
            )
        )

        if not parts["scheme"]:
            # Sometimes users enter urls without the scheme (intentionally or
            # otherwise). These are valid in browsers, but possibly not for our
            # validator, so we'll use the provided default.
            parts["scheme"] = self.scheme

        scheme = parts["scheme"]
        if scheme in ["http", "https", "ftp", "ftps"]:
            return self.validate_default(parts, verify_exists=verify_exists)

        elif scheme != "url" and hasattr(self, "validate_" + scheme):
            validator = getattr(self, "validate_" + scheme)
            return validator(parts, verify_exists=verify_exists)
        else:
            warnings.warn('Validator not found for scheme: "{0}".'.format(scheme))
            return False

    def check_link(self, instance, verify_exists=False):
        """
        Return True if the plugin instance's url form is valid. This method is
        encouraged to call upon self.validate_url().

        :param instance: Plugin instance
        :param verify_exists:
        :return: LinkReport
        """
        raise NotImplementedError("Must be implemented in sub-class.")
