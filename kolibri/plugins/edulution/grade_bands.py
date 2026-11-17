"""
Grade bands for the LSHE deployment: each classroom has a band (e.g. "G4-5"),
and each band allows a set of channels. Coaches can only assign content from
the band's channels, and restricted learners only see content from the
channels of their classes' bands.

Set up with set_band_channels.py and set_class_band.py in kolibri_helper_scripts
(lshe/), which write the models in models.py.
Enforcement is on unless LSHE_GRADE_BANDS=off (see lshe_settings). The hook
that applies these rules is GradeBandRestrictionHook in kolibri_plugin.py.
"""


def _teacher_channels():
    from kolibri.plugins.edulution.lshe_settings import teacher_channel_ids

    try:
        return set(teacher_channel_ids())
    except ValueError:
        # A malformed setting must not open anything up; the helper scripts
        # (set_band_channels.py, lshe_report.py) report the bad value.
        return set()


def band_channel_ids(band):
    """A band's channels. Teacher channels are never included, even if added."""
    from kolibri.plugins.edulution.models import GradeBandChannel

    return (
        frozenset(
            GradeBandChannel.objects.filter(band=band).values_list(
                "channel_id", flat=True
            )
        )
        - _teacher_channels()
    )


def classroom_band(classroom_id):
    from kolibri.plugins.edulution.models import ClassroomBand

    return (
        ClassroomBand.objects.filter(classroom_id=classroom_id)
        .values_list("band", flat=True)
        .first()
    )


def allowed_channel_ids_for_learner(user):
    """Channels of the bands of every class the user is in, minus teacher channels."""
    from kolibri.core.auth.constants import collection_kinds
    from kolibri.core.auth.models import Membership
    from kolibri.plugins.edulution.models import ClassroomBand
    from kolibri.plugins.edulution.models import GradeBandChannel

    classroom_ids = Membership.objects.filter(
        user_id=user.id, collection__kind=collection_kinds.CLASSROOM
    ).values("collection_id")
    bands = ClassroomBand.objects.filter(classroom_id__in=classroom_ids).values("band")
    return (
        set(
            GradeBandChannel.objects.filter(band__in=bands).values_list(
                "channel_id", flat=True
            )
        )
        - _teacher_channels()
    )
