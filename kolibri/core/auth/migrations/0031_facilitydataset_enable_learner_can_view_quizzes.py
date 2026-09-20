# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


def enable_learner_can_view_quizzes(apps, schema_editor):
    FacilityDataset = apps.get_model("kolibriauth", "FacilityDataset")
    FacilityDataset.objects.filter(learner_can_view_quizzes=False).update(
        learner_can_view_quizzes=True
    )


def revert_learner_can_view_quizzes(apps, schema_editor):
    # Data migrations are one-way here: there is no way to tell which
    # facilities had this explicitly set to False on purpose (vs. never
    # touched) before this migration ran, so reversing is a no-op rather
    # than guessing.
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('kolibriauth', '0030_facilitydataset_learner_can_view_quizzes'),
    ]

    operations = [
        migrations.AlterField(
            model_name='facilitydataset',
            name='learner_can_view_quizzes',
            field=models.BooleanField(default=True),
        ),
        migrations.RunPython(
            enable_learner_can_view_quizzes, revert_learner_can_view_quizzes
        ),
    ]
