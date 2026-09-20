# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import django.db.models.deletion
from django.db import migrations
from django.db import models

import kolibri.core.fields


class Migration(migrations.Migration):

    dependencies = [
        ("kolibriauth", "0029_facilitydataset_content_visibility_settings"),
        ("lessons", "0004_nullable_created_by_assigned_by"),
    ]

    operations = [
        migrations.CreateModel(
            name="LearnerResourceLock",
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
                ("contentnode_id", models.CharField(max_length=32)),
                ("created", kolibri.core.fields.DateTimeTzField()),
                (
                    "lesson",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="learner_resource_locks",
                        to="lessons.Lesson",
                    ),
                ),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="resource_locks",
                        to="kolibriauth.FacilityUser",
                    ),
                ),
            ],
        ),
        migrations.AlterUniqueTogether(
            name="learnerresourcelock",
            unique_together=set([("lesson", "user", "contentnode_id")]),
        ),
    ]
