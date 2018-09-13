# -*- coding: utf-8 -*-

# Standard library imports
from __future__ import unicode_literals

from django.conf.urls import url
from django.utils.translation import ugettext_lazy as _
from django.views.generic import TemplateView

from .views import AnalyzeView

app_name = "link-manager"

urlpatterns = [
    url(r'^$', TemplateView.as_view(template_name='djangocms_link_manager/start.html'), name="start"),
    url(_(r'^analyze/$'), AnalyzeView.as_view(), name="analyze"),
]
