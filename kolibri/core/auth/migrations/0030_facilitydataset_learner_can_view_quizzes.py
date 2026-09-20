# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('kolibriauth', '0029_facilitydataset_content_visibility_settings'),
    ]

    operations = [
        migrations.AddField(
            model_name='facilitydataset',
            name='learner_can_view_quizzes',
            field=models.BooleanField(default=False),
        ),
    ]
