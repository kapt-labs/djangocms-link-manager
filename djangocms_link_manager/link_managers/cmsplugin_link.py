# -*- coding: utf-8 -*-

from __future__ import unicode_literals
from django.utils.translation import ugettext as _
from django.urls import NoReverseMatch

from ..link_manager import LinkManager, LinkReport, hyperlink_should_be_audited


class CMSPluginLinkLinkManager(LinkManager):

    def check_link(self, instance, verify_exists=False):
        if instance.mailto or instance.phone or instance.anchor:
            return []

        valid = False

        if instance.internal_link is not None:
            try:
                url = instance.internal_link.get_absolute_url(instance.language)
            except NoReverseMatch:
                url = None
            else:
                valid = True

        elif instance.external_link != '':
            url = instance.external_link
            if not hyperlink_should_be_audited(url):
                return []
            valid = self.validate_url(url, verify_exists=verify_exists)

        elif instance.file_link is not None:
            url = instance.file_link.url
            valid = self.validate_url(url, verify_exists=verify_exists)

        elif instance.get_children().count() > 0:
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
