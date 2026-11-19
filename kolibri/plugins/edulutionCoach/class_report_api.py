"""
The coach's Monthly reports page for a class: the LSHE figures for a day,
week or month (kolibri.plugins.edulution.lshe_metrics, the same figures as
the monthly report for UNESCO), with a chart series, the last six months,
the band's topic progress and a row per learner.

    GET /edulutioncoach/api/classreport/<class_id>/?period=month&date=2026-11-18

`period` is day, week or month (default month); `date` (YYYY-MM-DD, default
today in the report's time zone) picks which one. Only the class's coaches
and the facility's admins may read it: the learner rows carry names.
"""
import datetime
import os

from django.shortcuts import get_object_or_404
from rest_framework import permissions
from rest_framework import viewsets
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response

from kolibri.core.auth import models as auth_models
from kolibri.core.lessons.models import Lesson
from kolibri.plugins.edulution.lshe_metrics import class_report
from kolibri.plugins.edulution.lshe_metrics import MONTH
from kolibri.plugins.edulution.lshe_metrics import PERIODS
from kolibri.plugins.edulution.lshe_metrics import report_timezone
from kolibri.plugins.edulutionCoach.class_summary_api import (
    ClassSummaryPermissions,
)
from kolibri.plugins.edulutionCoach.class_summary_api import get_band_topic_progress
from kolibri.plugins.edulutionCoach.class_summary_api import serialize_lessons


def _day(value):
    if not value:
        return datetime.datetime.now(report_timezone()).date()
    try:
        return datetime.datetime.strptime(value, "%Y-%m-%d").date()
    except ValueError:
        raise ValidationError({"date": "Use YYYY-MM-DD."})


class ClassReportViewSet(viewsets.ViewSet):
    permission_classes = (permissions.IsAuthenticated, ClassSummaryPermissions)

    def retrieve(self, request, pk):
        classroom = get_object_or_404(auth_models.Classroom, id=pk)
        period = request.query_params.get("period", MONTH)
        if period not in PERIODS:
            raise ValidationError({"period": "Use one of: " + ", ".join(PERIODS)})
        report = class_report(classroom, period, _day(request.query_params.get("date")))

        names = dict(
            auth_models.FacilityUser.objects.filter(
                id__in=[row["id"] for row in report["learners"]]
            ).values_list("id", "full_name")
        )
        for row in report["learners"]:
            row["name"] = names.get(row["id"], "")
        report["learners"].sort(key=lambda row: row["name"].lower())

        report["class"] = {"id": classroom.id, "name": classroom.name}
        report["centre_code"] = os.environ.get("KOLIBRI_CENTRE_CODE", "")
        report["topics"] = get_band_topic_progress(
            classroom,
            [row["id"] for row in report["learners"]],
            serialize_lessons(Lesson.objects.filter(collection=classroom)),
        )
        return Response(report)
