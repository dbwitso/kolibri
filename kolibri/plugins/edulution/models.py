"""
Models for the LSHE (UNESCO pilot) deployment.

Kolibri registers plugin apps under their full module path as the app label
(see kolibri.plugins.utils.settings), so every model here sets an explicit,
dot-free db_table.

None of these models are synced (this deployment never syncs Kolibri
servers), so they are plain Django models, not Morango syncable models.
"""
from django.db import models

from kolibri.core.auth.models import Classroom
from kolibri.core.auth.models import FacilityUser
from kolibri.core.fields import DateTimeTzField


class LSHEMonthlyEnrolment(models.Model):
    """
    Which class (and gender) each learner was in for a reported month.

    Kolibri keeps no history of class memberships, so `lshereport` takes this
    snapshot the first time a finished month is reported and reuses it on
    every re-run, which keeps the monthly figures the same.

    Holds no names, usernames or birth years: only the Kolibri user id (so the
    report can join activity logs), the class name and gender. Rows are
    removed with the user.
    """

    month = models.CharField(max_length=7, db_index=True)  # "YYYY-MM"
    user = models.ForeignKey(FacilityUser, on_delete=models.CASCADE)
    # "" means the learner was in no class at the end of the month.
    class_name = models.CharField(max_length=100, blank=True, default="")
    gender = models.CharField(max_length=16)
    # Soft-deleted learners still count towards "reached" figures (they did
    # complete content) but not towards enrolment.
    deleted = models.BooleanField(default=False)
    taken_at = DateTimeTzField()

    class Meta:
        db_table = "edulution_lshe_monthly_enrolment"
        unique_together = ("month", "user", "class_name")


# Grade bands. Kolibri's dotted plugin app label ("kolibri.plugins.edulution")
# breaks ForeignKeys between two models of this plugin on Django 1.11, so a
# band is identified by its name in both tables rather than by a GradeBand row.

BAND_NAME_MAX = 20


class GradeBandChannel(models.Model):
    """A channel whose content may be assigned to classes in a band."""

    band = models.CharField(max_length=BAND_NAME_MAX, db_index=True)  # e.g. "G4-5"
    # Hex channel id, as stored on ContentNode.channel_id.
    channel_id = models.CharField(max_length=32)

    class Meta:
        db_table = "edulution_grade_band_channel"
        unique_together = ("band", "channel_id")


class ClassroomBand(models.Model):
    """The grade band of a classroom. A classroom has at most one band."""

    classroom = models.OneToOneField(
        Classroom, on_delete=models.CASCADE, related_name="grade_band_link"
    )
    band = models.CharField(max_length=BAND_NAME_MAX, db_index=True)

    class Meta:
        db_table = "edulution_classroom_band"
