# -*- coding: utf-8 -*-

from __future__ import unicode_literals
from django.utils.translation import ugettext as _
from django.core.urlresolvers import NoReverseMatch

from ..link_manager import LinkManager, LinkReport


class CMSPluginLinkLinkManager(LinkManager):

    def check_link(self, instance, verify_exists=False):
        valid = False

        if instance.internal_link is not None:
            try:
                url = instance.internal_link.get_absolute_url(instance.language)
            except NoReverseMatch:
                url = None
            else:
                valid = True

        elif instance.external_link is not '':
            url = instance.external_link
            valid = self.validate_url(url, verify_exists=verify_exists)

        elif instance.mailto is not '':
            url = instance.mailto
            valid = self.validate_mailto(url, verify_exists=verify_exists)

        elif instance.phone is not '':
            url = instance.phone
            valid = self.validate_tel(url, verify_exists=verify_exists)

        elif instance.file_link is not None:
            url = instance.file_link.url
            valid = self.validate_url(url, verify_exists=verify_exists)

        elif instance.get_children() > 0:
            url = _('Invalid link (no URL) but with children plugins')

        else:
            url = _('Invalid link (no URL)')


        if instance.name == "":
            name = _("Link without label")
        else:
            name = instance.name

        return LinkReport(
            valid=valid,
            text=name,
            url=url,
        )
