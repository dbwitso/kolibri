from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.decorators import action
from rest_framework.response import Response

from .serializers import LessonSerializer
from kolibri.core.api import ValuesViewset
from kolibri.core.auth.api import KolibriAuthPermissions
from kolibri.core.auth.api import KolibriAuthPermissionsFilter
from kolibri.core.auth.constants.collection_kinds import ADHOCLEARNERSGROUP
from kolibri.core.auth.models import FacilityUser
from kolibri.core.content.models import ContentNode
from kolibri.core.content.utils.annotation import total_file_size
from kolibri.core.lessons.models import LearnerResourceLock
from kolibri.core.lessons.models import Lesson
from kolibri.core.lessons.models import LessonAssignment
from kolibri.core.query import annotate_array_aggregate


def _ensure_raw_dict(d):
    if hasattr(d, "dict"):
        d = d.dict()
    return dict(d)


class LessonPermissions(KolibriAuthPermissions):
    # Overrides the default validator to sanitize the Lesson POST Payload
    # before validation
    def validator(self, request, view, datum):
        model = view.get_serializer_class().Meta.model
        validated_data = view.get_serializer().to_internal_value(
            _ensure_raw_dict(datum)
        )
        # Cannot have create assignments without creating the Lesson first,
        # so this doesn't try to validate the Lesson with a non-empty lesson_assignments list
        validated_data.pop("lesson_assignments", [])
        validated_data.pop("learner_ids", [])
        return request.user.can_create(model, validated_data)


def _map_lesson_classroom(item):
    return {
        "id": item.pop("collection__id"),
        "name": item.pop("collection__name"),
        "parent": item.pop("collection__parent_id"),
    }


class LessonViewset(ValuesViewset):
    serializer_class = LessonSerializer
    filter_backends = (KolibriAuthPermissionsFilter, DjangoFilterBackend)
    filter_fields = ("collection", "id")
    permission_classes = (LessonPermissions,)
    queryset = Lesson.objects.all().order_by("-date_created")

    values = (
        "id",
        "title",
        "description",
        "resources",
        "is_active",
        "collection",  # classroom
        "collection__id",
        "collection__name",
        "collection__parent_id",
        "created_by",
        "lesson_assignment_collections",
    )

    field_map = {
        "classroom": _map_lesson_classroom,
        "lesson_assignments": "lesson_assignment_collections",
    }

    def consolidate(self, items, queryset):
        if items:
            lesson_ids = [l["id"] for l in items]
            adhoc_assignments = LessonAssignment.objects.filter(
                lesson_id__in=lesson_ids, collection__kind=ADHOCLEARNERSGROUP
            )
            adhoc_assignments = annotate_array_aggregate(
                adhoc_assignments, learner_ids="collection__membership__user_id"
            )
            adhoc_assignments = {
                a["lesson"]: a
                for a in adhoc_assignments.values("collection", "lesson", "learner_ids")
            }
            for item in items:
                if item["id"] in adhoc_assignments:
                    adhoc_assignment = adhoc_assignments[item["id"]]
                    item["learner_ids"] = adhoc_assignments[item["id"]]["learner_ids"]
                    item["lesson_assignments"] = [
                        i
                        for i in item["lesson_assignments"]
                        if i != adhoc_assignment["collection"]
                    ]
                else:
                    item["learner_ids"] = []
                item["resources"] = item["resources"] or []

        return items

    def annotate_queryset(self, queryset):
        return annotate_array_aggregate(
            queryset, lesson_assignment_collections="lesson_assignments__collection"
        )

    @action(detail=True, methods=["post"], url_path="unlock-learner-resource")
    def unlock_learner_resource(self, request, pk=None):
        """
        Remove a learner's auto-created completion lock on a resource in
        this Lesson, so they can access it again. Coach/admin only, enforced
        the same way as any other update to this Lesson.
        """
        lesson = self.get_object()
        user_id = request.data.get("user_id")
        contentnode_id = request.data.get("contentnode_id")
        if not user_id or not contentnode_id:
            return Response(
                {"error": "user_id and contentnode_id are required"}, status=400
            )
        user = get_object_or_404(FacilityUser, id=user_id)
        LearnerResourceLock.objects.filter(
            lesson=lesson, user=user, contentnode_id=contentnode_id
        ).delete()
        return Response({"lesson_id": lesson.id, "user_id": user_id, "contentnode_id": contentnode_id})

    @action(detail=False)
    def size(self, request, **kwargs):
        lessons = self.filter_queryset(self.get_queryset())
        lessons_set = []
        for lesson in lessons:
            lesson_size = {}
            resource_nodes = ContentNode.objects.filter(
                id__in=[r["contentnode_id"] for r in lesson.resources]
            )
            lesson_size[lesson.id] = total_file_size(resource_nodes)
            lessons_set.append(lesson_size)

        return Response(lessons_set)
