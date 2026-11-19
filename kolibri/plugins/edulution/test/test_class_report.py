"""
The coach's Monthly reports page: LSHE figures for a class by day, week and
month, from lshe_metrics (the same figures as the monthly report for
UNESCO). All data here is invented.
"""
import datetime
import uuid

import pytz
from django.test import override_settings
from django.urls import reverse
from le_utils.constants import content_kinds
from rest_framework.test import APITestCase

from kolibri.core.auth.constants.demographics import FEMALE
from kolibri.core.auth.constants.demographics import MALE
from kolibri.core.auth.models import FacilityUser
from kolibri.core.logger.models import ContentSessionLog
from kolibri.core.logger.models import ContentSummaryLog
from kolibri.core.logger.models import UserSessionLog
from kolibri.plugins.edulution.lshe_metrics import class_report
from kolibri.plugins.edulution.lshe_metrics import period_bounds
from kolibri.plugins.edulution.models import LSHEMonthlyEnrolment
from kolibri.plugins.edulution.test.test_grade_bands import BandFixture
from kolibri.plugins.edulution.test.test_grade_bands import PASSWORD

LUSAKA = pytz.timezone("Africa/Lusaka")
TEACHER_CHANNEL = uuid.uuid4().hex


def at(day, hour=10, minute=0, month=11):
    return LUSAKA.localize(datetime.datetime(2026, month, day, hour, minute))


class ReportData(BandFixture):
    @classmethod
    def setUpTestData(cls):
        cls.build()
        cls.learner.gender = FEMALE
        cls.learner.save()
        cls.boy = FacilityUser.objects.create(
            username="grade4.boy", facility=cls.facility, gender=MALE
        )
        cls.lower.add_member(cls.boy)
        cls.unknown = FacilityUser.objects.create(
            username="grade4.unknown", facility=cls.facility
        )
        cls.lower.add_member(cls.unknown)

        # Girl: two sessions (16 and 18 Nov), finishes a video on the 18th,
        # watched 600 s. Boy: one session on 18 Nov, no completion; also a
        # completion in October (reached before November).
        cls.session(cls.learner, at(16, 9), at(16, 9, 30))
        cls.session(cls.learner, at(18, 10), at(18, 10, 20))
        cls.session(cls.boy, at(18, 10), at(18, 10, 10))
        cls.done(cls.learner, at(18, 10, 15), channel=cls.g45_channel)
        cls.done(cls.boy, at(20, 9, month=10), channel=cls.g45_channel)
        cls.video(cls.learner, at(18, 10, 15), 600, cls.g45_channel)
        # Teacher channel activity: never counted.
        cls.done(cls.unknown, at(18, 11), channel=TEACHER_CHANNEL)
        cls.video(cls.unknown, at(18, 11), 900, TEACHER_CHANNEL)

    @staticmethod
    def session(user, start, end):
        log = UserSessionLog.objects.create(user=user)
        UserSessionLog.objects.filter(pk=log.pk).update(
            start_timestamp=start, last_interaction_timestamp=end
        )

    @staticmethod
    def done(user, when, channel):
        ContentSummaryLog.objects.create(
            user=user,
            content_id=uuid.uuid4().hex,
            channel_id=channel,
            kind=content_kinds.VIDEO,
            progress=1,
            start_timestamp=when,
            end_timestamp=when,
            completion_timestamp=when,
        )

    @staticmethod
    def video(user, ended, seconds, channel):
        ContentSessionLog.objects.create(
            user=user,
            content_id=uuid.uuid4().hex,
            channel_id=channel,
            kind=content_kinds.VIDEO,
            start_timestamp=ended,
            end_timestamp=ended,
            time_spent=seconds,
            progress=0.5,
        )


@override_settings(
    LSHE_GRADE_BANDS="on",
    LSHE_TEACHER_CHANNEL_IDS=TEACHER_CHANNEL,
    LSHE_REPORT_TIMEZONE="Africa/Lusaka",
)
class ClassReportFiguresTestCase(ReportData, APITestCase):
    def report(self, period, day, now=None):
        return class_report(
            self.lower, period, day, now=now or at(25, 12).astimezone(pytz.utc)
        )

    def test_month_by_gender(self):
        totals = self.report("month", datetime.date(2026, 11, 3))["totals"]
        everyone = totals["ALL"]
        self.assertEqual(everyone["enrolled_learners"], 3)
        self.assertEqual(everyone["active_learners"], 2)
        self.assertEqual(everyone["sessions"], 3)
        self.assertEqual(everyone["reached_new"], 1)  # the girl
        self.assertEqual(everyone["reached_cumulative"], 2)  # + the boy, October
        self.assertEqual(everyone["completions"], 1)  # teacher channel left out
        self.assertEqual(everyone["video_watch_seconds"], 600)
        self.assertEqual(everyone["logged_in_seconds"], (30 + 20 + 10) * 60)
        self.assertEqual(totals["FEMALE"]["completions"], 1)
        self.assertEqual(totals["MALE"]["reached_new"], 0)
        self.assertEqual(totals["MALE"]["reached_cumulative"], 1)
        self.assertEqual(totals["NOT_SPECIFIED"]["completions"], 0)

    def test_week_series_by_day(self):
        report = self.report("week", datetime.date(2026, 11, 18))
        self.assertEqual(report["start"][:10], "2026-11-16")
        series = {row["key"]: row for row in report["series"]}
        self.assertEqual(len(series), 7)
        self.assertEqual(series["2026-11-16"]["active_learners"], 1)
        self.assertEqual(series["2026-11-18"]["active_learners"], 2)
        self.assertEqual(series["2026-11-18"]["completions"], 1)
        self.assertEqual(series["2026-11-18"]["video_watch_seconds"], 600)
        self.assertEqual(series["2026-11-17"]["sessions"], 0)

    def test_day_series_by_hour(self):
        report = self.report("day", datetime.date(2026, 11, 18))
        self.assertEqual(len(report["series"]), 24)
        by_hour = {row["key"]: row for row in report["series"]}
        self.assertEqual(by_hour[10]["sessions"], 2)
        self.assertEqual(report["totals"]["ALL"]["active_learners"], 2)

    def test_six_month_trend(self):
        trend = self.report("month", datetime.date(2026, 11, 3))["trend"]
        self.assertEqual(
            [m["month"] for m in trend],
            ["2026-06", "2026-07", "2026-08", "2026-09", "2026-10", "2026-11"],
        )
        self.assertEqual(trend[4]["reached_new"], 1)  # the boy in October
        self.assertEqual(trend[5]["reached_cumulative"], 2)

    def test_learner_rows(self):
        rows = {
            r["id"]: r
            for r in self.report("month", datetime.date(2026, 11, 3))["learners"]
        }
        girl = rows[self.learner.id]
        self.assertEqual(girl["sessions"], 2)
        self.assertTrue(girl["reached"])
        self.assertTrue(girl["reached_new"])
        self.assertEqual(girl["video_watch_seconds"], 600)
        self.assertFalse(rows[self.unknown.id]["reached"])

    def test_finished_month_uses_the_saved_class_record(self):
        # The monthly report saved October with only the girl in Grade 4 A.
        LSHEMonthlyEnrolment.objects.create(
            month="2026-10",
            user=self.learner,
            class_name=self.lower.name,
            gender=FEMALE,
            taken_at=at(1, month=11),
        )
        report = self.report("month", datetime.date(2026, 10, 5))
        self.assertEqual(report["class_record_month"], "2026-10")
        self.assertEqual(report["totals"]["ALL"]["enrolled_learners"], 1)
        # A month still running uses today's class.
        self.assertIsNone(
            self.report("month", datetime.date(2026, 11, 5))["class_record_month"]
        )

    def test_period_bounds_in_lusaka(self):
        start, end, buckets = period_bounds("month", datetime.date(2026, 2, 10), LUSAKA)
        self.assertEqual(start, LUSAKA.localize(datetime.datetime(2026, 2, 1)))
        self.assertEqual(end, LUSAKA.localize(datetime.datetime(2026, 3, 1)))
        self.assertEqual(len(buckets), 28)


@override_settings(LSHE_GRADE_BANDS="on", LSHE_TEACHER_CHANNEL_IDS=TEACHER_CHANNEL)
class ClassReportAPITestCase(ReportData, APITestCase):
    def get(self, user, **params):
        self.client.login(
            username=user.username, password=PASSWORD, facility=self.facility
        )
        return self.client.get(
            reverse(
                "kolibri:kolibri.plugins.edulutionCoach:classreport-detail",
                kwargs={"pk": self.lower.id},
            ),
            params,
        )

    def test_coach_reads_it_with_names(self):
        response = self.get(self.coach, period="week", date="2026-11-18")
        self.assertEqual(response.status_code, 200, response.content)
        self.assertEqual(response.data["class"]["name"], self.lower.name)
        self.assertIn(
            "grade4.boy", [r["name"] or "grade4.boy" for r in response.data["learners"]]
        )
        self.assertEqual(len(response.data["series"]), 7)
        self.assertIn("topics", response.data)

    def test_learner_cannot_read_it(self):
        self.learner.set_password(PASSWORD)
        self.learner.save()
        self.assertIn(self.get(self.learner).status_code, (403, 404))

    def test_bad_period_or_date(self):
        self.assertEqual(self.get(self.coach, period="year").status_code, 400)
        self.assertEqual(self.get(self.coach, date="18/11/2026").status_code, 400)
