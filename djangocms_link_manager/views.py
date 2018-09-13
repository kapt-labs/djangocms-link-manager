# -*- coding: utf-8 -*-

from django.core.management import call_command
from django.views.generic import TemplateView


class AnalyzeView(TemplateView):
    template_name = 'djangocms_link_manager/end.html'

    def get(self, request, *args, **kwargs):
        verify_exists = 'verify_exists' in request.GET

        call_command('check_links', verify_exists=verify_exists, mail_managers=True)

        return super(AnalyzeView, self).get(request, *args, **kwargs)
