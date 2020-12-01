# -*- coding: utf-8 -*-
try:
    from StringIO import StringIO  # for Python 2
except ImportError:
    from io import StringIO  # for Python 3


from django.core.management import call_command
from django.views.generic import TemplateView


class AnalyzeView(TemplateView):
    template_name = 'djangocms_link_manager/end.html'

    def get(self, request, *args, **kwargs):
        verify_exists = 'verify_exists' in request.GET
        page_id = request.GET.get('page_id', None)
        host = request.get_host()
        is_mail_managers = page_id is None

        out = StringIO()
        call_command(
            'check_links',
            verify_exists=verify_exists,
            only_page_with_id=page_id,
            mail_managers=is_mail_managers,
            host=host,
            stdout=out
        )

        context = {
            "is_mail_managers": is_mail_managers,
            "page_id": page_id,
            "output": out.getvalue()
        }
        return self.render_to_response(context)
