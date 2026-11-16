"""
Deployment settings for the LSHE (UNESCO pilot) features, read from the
environment first and then from Django settings.

    LSHE_GRADE_BANDS          "off" turns grade-band enforcement off (for
                              deployments of this plugin that are not LSHE).
                              Any other value, or unset, leaves it on: a class
                              with no band can then receive no assignments.
    LSHE_TEACHER_CHANNEL_IDS  comma- or space-separated channel ids of the
                              teacher channels: left out of reports, never
                              allowed in a grade band.
"""
import os
import re
import uuid

from django.conf import settings

FALSY = ("0", "false", "no", "off")


def _setting(name, default):
    value = os.environ.get(name)
    if value is None:
        value = getattr(settings, name, default)
    return value


def grade_bands_enforced():
    return str(_setting("LSHE_GRADE_BANDS", "on")).strip().lower() not in FALSY


def normalise_channel_id(value):
    """Hex channel id, or ValueError."""
    return uuid.UUID(str(value).strip()).hex


def teacher_channel_ids():
    """Sorted list of hex channel ids, or ValueError naming a bad id."""
    raw = _setting("LSHE_TEACHER_CHANNEL_IDS", "")
    values = (
        list(raw) if isinstance(raw, (list, tuple, set)) else re.split(r"[\s,]+", raw)
    )
    ids = set()
    for value in values:
        if not value:
            continue
        try:
            ids.add(normalise_channel_id(value))
        except ValueError:
            raise ValueError(
                "LSHE_TEACHER_CHANNEL_IDS has an invalid channel id: {!r}".format(value)
            )
    return sorted(ids)
