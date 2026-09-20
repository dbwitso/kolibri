"""
Restricts the content library that a plain Learner can see to only resources
that a Coach/Admin has explicitly assigned to them via an active Lesson or
Quiz. Learners with no Role (i.e. not a Coach or Admin) and who are not a
superuser are considered "restricted learners" for this purpose.
"""
from kolibri.core.exams.models import Exam
from kolibri.core.exams.models import ExamAssignment
from kolibri.core.lessons.models import Lesson
from kolibri.core.lessons.models import LessonAssignment


def is_restricted_learner(user):
    """
    :type user: kolibri.core.auth.models.FacilityUser
    :rtype: bool
    """
    if not getattr(user, "is_authenticated", False):
        return False
    if user.is_superuser:
        return False
    return not user.roles.exists()


def get_assigned_content_ids(user):
    """
    The set of ContentNode ids that `user` may see: resources from any active
    Lesson, and exercises from any active Quiz, assigned (directly, via a
    Learner Group, or via their Classroom) to them.

    :type user: kolibri.core.auth.models.FacilityUser
    :rtype: set
    """
    content_ids = set()

    lesson_ids = LessonAssignment.objects.filter(
        collection__membership__user_id=user.id, lesson__is_active=True
    ).values_list("lesson_id", flat=True)
    for resources in Lesson.objects.filter(id__in=lesson_ids).values_list(
        "resources", flat=True
    ):
        for resource in resources:
            content_ids.add(resource["contentnode_id"])

    exam_ids = ExamAssignment.objects.filter(
        collection__membership__user_id=user.id, exam__active=True
    ).values_list("exam_id", flat=True)
    for question_sources in Exam.objects.filter(id__in=exam_ids).values_list(
        "question_sources", flat=True
    ):
        for question_source in question_sources:
            content_ids.add(question_source["exercise_id"])

    return content_ids
