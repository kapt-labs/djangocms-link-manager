from django.contrib import admin

from .models import LinkCheckIgnoredLink


@admin.register(LinkCheckIgnoredLink)
class LinkCheckIgnoredLinkAdmin(admin.ModelAdmin):
    list_display = ("url", "comment", "active", "created")
    list_filter = ("active",)
    search_fields = ("url", "comment", "normalized_url")
    readonly_fields = ("normalized_url", "created")
