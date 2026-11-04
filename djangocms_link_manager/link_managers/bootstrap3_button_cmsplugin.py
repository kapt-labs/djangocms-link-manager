# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from django.urls import NoReverseMatch

from ..link_manager import LinkManager, LinkReport, hyperlink_should_be_audited


class Bootstrap3ButtonCMSPluginLinkManager(LinkManager):

    def check_link(self, instance, verify_exists=False):
        if instance.link_phone or instance.link_mailto:
            return []

        valid = False
        url = None

        if instance.link_url:
            url = instance.link_url
            if not hyperlink_should_be_audited(url):
                return []
            valid = self.validate_url(url, verify_exists=verify_exists)
        elif instance.link_page:
            try:
                url = instance.link_page.get_absolute_url(instance.language)
            except NoReverseMatch:
                url = None
                valid = False
            else:
                valid = True

        elif instance.link_file:
            url = instance.link_file.url
            valid = self.validate_url(url, verify_exists=verify_exists)

        else:
            return []

        return LinkReport(
            valid=valid,
            text=instance.label,
            url=url,
        )
