# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('kolibriauth', '0028_facilitydataset_learner_can_view_lessons'),
    ]

    operations = [
        migrations.AddField(
            model_name='facilitydataset',
            name='learner_can_search_content',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='facilitydataset',
            name='learner_can_view_recent_content',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='facilitydataset',
            name='learner_can_view_other_libraries',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='facilitydataset',
            name='learner_can_view_recommended_content',
            field=models.BooleanField(default=False),
        ),
    ]
