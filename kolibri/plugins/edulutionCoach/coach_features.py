"""
Coach features a facility admin can turn off on the facility's Settings
page: quizzes and groups. Each is a key in the facility's settings
(FacilityDataset.extra_fields), so it syncs with the facility. A missing key
means on, so nothing changes for a facility until its admin turns one off.

Turning one off hides it from the coach pages: the Reports and Plan tabs,
the Class home, the learner and lesson reports, and the choice of who a
lesson is for. Its pages send the coach to the Class home instead.
"""
from kolibri.core.auth.models import Facility

QUIZZES = "coach_quizzes"
GROUPS = "coach_groups"


def coach_features(dataset):
    extra = (dataset.extra_fields if dataset else None) or {}
    return {
        "quizzes": extra.get(QUIZZES) is not False,
        "groups": extra.get(GROUPS) is not False,
    }


def coach_features_by_facility():
    """{facility_id: {"quizzes": bool, "groups": bool}} for every facility."""
    return {
        facility.id: coach_features(facility.dataset)
        for facility in Facility.objects.select_related("dataset")
    }
