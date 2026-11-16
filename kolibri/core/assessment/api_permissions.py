"""
Access control for the /api/assessments/ endpoints.

Most assessment ViewSets were written without permission_classes, and
Kolibri sets no DEFAULT_PERMISSION_CLASSES, so DRF's AllowAny applied:
anyone on the network, signed in or not, could read learners' assessment
records and call the write endpoints. Every assessment ViewSet now uses the
classes below.

- Coach endpoints (used by the edulutionCoach UI) need a coach or admin role
  for the classroom concerned.
- Learner endpoints (used by the edulution learner UI) allow the learner
  themselves, or a coach/admin for that learner.
- When assessments are switched off (LSHE_DISABLE_ASSESSMENTS, used by the
  LSHE deployment, which carries no adaptive assessments) every endpoint
  refuses.
"""
import os

from django.conf import settings
from django.core.exceptions import ValidationError
from rest_framework.permissions import BasePermission

from kolibri.core.auth.constants import role_kinds
from kolibri.core.auth.models import Collection
from kolibri.core.auth.models import FacilityUser

COACH_KINDS = (role_kinds.ADMIN, role_kinds.COACH)
TRUTHY = ("1", "true", "yes", "on")


def assessments_disabled():
    value = os.environ.get("LSHE_DISABLE_ASSESSMENTS")
    if value is None:
        value = getattr(settings, "LSHE_DISABLE_ASSESSMENTS", False)
    return str(value).strip().lower() in TRUTHY


def _get(model, **lookup):
    """model.objects.get(**lookup), or None for a missing or malformed id."""
    try:
        return model.objects.get(**lookup)
    except (model.DoesNotExist, ValueError, TypeError, ValidationError):
        return None


def _assessment_models():
    # Imported lazily: kolibri.core.assessment.models imports from auth.
    from kolibri.core.assessment import models

    return models


def _signed_in(user):
    return bool(user and user.is_authenticated and isinstance(user, FacilityUser))


class AssessmentsEnabled(BasePermission):
    message = "Assessments are switched off on this server."

    def has_permission(self, request, view):
        return not assessments_disabled()


class _CoachForCollection(BasePermission):
    """Signed-in coach/admin for the collection returned by get_collection()."""

    message = "You must be a coach or admin for this class."

    def get_collection(self, request, view):
        raise NotImplementedError

    def has_permission(self, request, view):
        if assessments_disabled() or not _signed_in(request.user):
            return False
        collection = self.get_collection(request, view)
        return collection is not None and request.user.has_role_for_collection(
            COACH_KINDS, collection
        )


class CoachForRequestCollection(_CoachForCollection):
    """Collection id in the request body (`collection`)."""

    def get_collection(self, request, view):
        return _get(Collection, id=request.data.get("collection"))


class CoachForPkCollection(_CoachForCollection):
    """The URL pk is a collection id."""

    def get_collection(self, request, view):
        return _get(Collection, id=view.kwargs.get("pk"))


class CoachForPkGroup(_CoachForCollection):
    """The URL pk is an ExamAssessmentGroup id."""

    def get_collection(self, request, view):
        group = _get(_assessment_models().ExamAssessmentGroup, id=view.kwargs.get("pk"))
        return group.collection if group else None


class CoachForPkAssessment(_CoachForCollection):
    """The URL pk is an ExamAssessment id."""

    def get_collection(self, request, view):
        assessment = _get(_assessment_models().ExamAssessment, id=view.kwargs.get("pk"))
        return assessment.collection if assessment else None


class CoachForRequestAssessment(_CoachForCollection):
    """ExamAssessment id in the request body (`assessment_id`)."""

    def get_collection(self, request, view):
        assessment = _get(
            _assessment_models().ExamAssessment, id=request.data.get("assessment_id")
        )
        return assessment.collection if assessment else None


class IsAnyCoach(BasePermission):
    """Signed in with a coach or admin role anywhere (or device superuser)."""

    message = "You must be a coach or admin."

    def has_permission(self, request, view):
        if assessments_disabled() or not _signed_in(request.user):
            return False
        user = request.user
        return user.is_superuser or user.roles.filter(kind__in=COACH_KINDS).exists()


class _SelfOrCoachOfLearner(BasePermission):
    """The learner returned by get_learner(), or a coach/admin for them."""

    message = "You can only see your own assessments."

    def get_learner(self, request, view):
        raise NotImplementedError

    def has_permission(self, request, view):
        if assessments_disabled() or not _signed_in(request.user):
            return False
        learner = self.get_learner(request, view)
        if learner is None:
            return False
        return learner.id == request.user.id or request.user.has_role_for_user(
            COACH_KINDS, learner
        )


class SelfOrCoachForQueryLearner(_SelfOrCoachOfLearner):
    """Learner id in a query parameter."""

    param = "learner_id"

    def get_learner(self, request, view):
        return _get(FacilityUser, id=request.query_params.get(self.param))


class SelfOrCoachForQueryLearners(SelfOrCoachForQueryLearner):
    # AssessmentHistoryReportViewSet takes a single id as `learner_ids`.
    param = "learner_ids"


class SelfOrCoachForPkLearner(_SelfOrCoachOfLearner):
    """The URL pk is a learner id."""

    def get_learner(self, request, view):
        return _get(FacilityUser, id=view.kwargs.get("pk"))


class SelfOrCoachForRequestAssessment(_SelfOrCoachOfLearner):
    """The learner of the ExamAssessment in the request body (`assessment_id`)."""

    def get_learner(self, request, view):
        assessment = _get(
            _assessment_models().ExamAssessment, id=request.data.get("assessment_id")
        )
        return assessment.learner if assessment else None
