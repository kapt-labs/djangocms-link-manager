from django.contrib.sites.models import Site
from django.core.exceptions import ValidationError
from django.db import models
from django.utils.translation import gettext_lazy as _

from .conf import settings as local_settings
from .ignored_links import clear_ignored_links_cache, normalize_url_for_ignore


class LinkCheckIgnoredLink(models.Model):
    """URL excluded from broken-link results after manual review."""

    url = models.CharField(
        verbose_name=_("URL"),
        max_length=2048,
        help_text=_("Full or site-relative href as it appears in the content."),
    )
    normalized_url = models.CharField(max_length=2048, editable=False, unique=True)
    comment = models.CharField(
        verbose_name=_("Comment"),
        max_length=255,
        blank=True,
    )
    active = models.BooleanField(verbose_name=_("Active"), default=True)
    created = models.DateTimeField(verbose_name=_("Ignored since"), auto_now_add=True)

    class Meta:
        verbose_name = _("Ignored link (link check)")
        verbose_name_plural = _("Ignored links (link check)")

    def __str__(self):
        return self.url

    def save(self, *args, **kwargs):
        site_domain = Site.objects.get_current().domain
        normalized = normalize_url_for_ignore(
            self.url,
            scheme=local_settings.IGNORE_URL_DEFAULT_SCHEME,
            netloc=site_domain,
        )
        if normalized is None:
            raise ValidationError({"url": _("Enter a valid URL.")})
        self.normalized_url = normalized
        super().save(*args, **kwargs)
        clear_ignored_links_cache()

    def delete(self, *args, **kwargs):
        super().delete(*args, **kwargs)
        clear_ignored_links_cache()
