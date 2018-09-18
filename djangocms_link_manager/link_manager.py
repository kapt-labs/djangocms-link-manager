# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import codecs
import phonenumbers
import requests
import socket
import warnings

from collections import OrderedDict
from hashlib import sha256

try:  # pragma: no cover
    # Python 3.x
    from urllib.parse import urlparse, urlunparse
except ImportError:  # pragma: no cover
    # Python 2.x
    from urlparse import urlparse, urlunparse

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import EmailValidator
from django.core.validators import URLValidator

import attr


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
    scheme = attr.ib(default='http')
    netloc = attr.ib(default='localhost:8000')

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
        if not parts['netloc']:
            # If there is no host/port, then this may be a link to a local
            # resource (media or static asset, etc.) Use the provided default.
            parts['netloc'] = self.netloc
        url = urlunparse(parts.values())
        try:
            validator(url)
        except ValidationError:
            return False
        else:
            if verify_exists:
                try:
                    response = requests.head(url)
                    if response.status_code == 500:  # Some sites do not handle HEAD requests correctly
                        raise requests.HTTPError
                    return 200 <= response.status_code < 400  # pragma: no cover
                except requests.HTTPError:
                    try:
                        response = requests.get(url)
                        return 200 <= response.status_code < 400  # pragma: no cover
                    except (requests.HTTPError,
                            requests.ConnectionError,
                            requests.TooManyRedirects,
                            UnicodeEncodeError,
                            socket.error):
                        return False
                except (requests.ConnectionError,
                        requests.TooManyRedirects,
                        UnicodeEncodeError,
                        socket.error):
                    return False
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
        digits58 = '123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz'

        def to_bytes(n, length):
            s = '%x' % n
            s = s.rjust(length * 2, '0')
            s = codecs.decode(s.encode("UTF-8"), 'hex_codec')
            return s

        def decode_base58(bc, length):
            n = 0
            for char in bc:
                n = n * 58 + digits58.index(char)
            return to_bytes(n, length)

        def check_bc(bc):
            bcbytes = decode_base58(bc, 25)
            return bcbytes[-4:] == sha256(sha256(bcbytes[:-4]).digest()).digest()[:4]

        btc_address = parts['path']
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
            parsed_num = phonenumbers.parse(phone_number, settings.LANGUAGE_CODE.upper())
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

        parts = OrderedDict(zip(
            ['scheme', 'netloc', 'path', 'params', 'query', 'fragment'],
            urlparse(url)
        ))

        if not parts['scheme']:
            # Sometimes users enter urls without the scheme (intentionally or
            # otherwise). These are valid in browsers, but possibly not for our
            # validator, so we'll use the provided default.
            parts['scheme'] = self.scheme

        scheme = parts['scheme']
        if scheme in ['http', 'https', 'ftp', 'ftps']:
            return self.validate_default(parts, verify_exists=verify_exists)

        elif scheme != 'url' and hasattr(self, 'validate_' + scheme):
            validator = getattr(self, 'validate_' + scheme)
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
        raise NotImplementedError('Must be implemented in sub-class.')
