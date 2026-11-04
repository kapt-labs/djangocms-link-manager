# -*- coding: utf-8 -*-

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="LinkCheckIgnoredLink",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "url",
                    models.CharField(
                        help_text="Absolute URL starting with http:// or https://.",
                        max_length=2048,
                        verbose_name="URL",
                    ),
                ),
                (
                    "normalized_url",
                    models.CharField(editable=False, max_length=2048, unique=True),
                ),
                (
                    "comment",
                    models.CharField(
                        blank=True, max_length=255, verbose_name="Comment"
                    ),
                ),
                ("active", models.BooleanField(default=True, verbose_name="Active")),
                (
                    "created",
                    models.DateTimeField(auto_now_add=True, verbose_name="Ignored since"),
                ),
            ],
            options={
                "verbose_name": "Ignored link (link check)",
                "verbose_name_plural": "Ignored links (link check)",
            },
        ),
    ]
