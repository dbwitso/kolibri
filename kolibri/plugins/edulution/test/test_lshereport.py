"""
Tests for `kolibri manage lshereport`. All learners are invented.

Reported month: 2026-03 in Africa/Lusaka (UTC+2), i.e.
[2026-02-28 22:00 UTC, 2026-03-31 22:00 UTC).
"""
import csv
import datetime
import io
import json
import os
import shutil
import tempfile
import uuid

import mock
import pytz
from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TestCase

from kolibri.core.auth.constants.demographics import FEMALE
from kolibri.core.auth.constants.demographics import MALE
from kolibri.core.auth.models import Classroom
from kolibri.core.auth.models import Facility
from kolibri.core.auth.models import FacilityUser
from kolibri.core.device.models import DevicePermissions
from kolibri.core.logger.models import ContentSessionLog
from kolibri.core.logger.models import ContentSummaryLog
from kolibri.core.logger.models import UserSessionLog
from kolibri.plugins.edulution.management.commands import lshereport
from kolibri.plugins.edulution.models import LSHEMonthlyEnrolment

LSHE_CHANNEL = uuid.uuid4().hex
TEACHER_CHANNEL = uuid.uuid4().hex
LUSAKA = pytz.timezone("Africa/Lusaka")


def lusaka(*args):
    return LUSAKA.localize(datetime.datetime(*args))


class LSHEReportTestCase(TestCase):
    def setUp(self):
        self.out_dir = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.out_dir)
        env = mock.patch.dict(
            os.environ,
            {
                "KOLIBRI_CENTRE_CODE": "TESTCENTRE",
                "LSHE_TEACHER_CHANNEL_IDS": TEACHER_CHANNEL,
            },
        )
        env.start()
        self.addCleanup(env.stop)
        os.environ.pop("LSHE_REPORT_TIMEZONE", None)

        self.facility = Facility.objects.create(name="Centre")
        self.class_a = Classroom.objects.create(name="Grade 5 A", parent=self.facility)
        self.class_b = Classroom.objects.create(name="Grade 6 A", parent=self.facility)
        joined = lusaka(2026, 1, 5)

        def learner(username, gender, classroom):
            user = FacilityUser.objects.create(
                username=username,
                full_name="Secret " + username,
                facility=self.facility,
                gender=gender,
                birth_year="2014",
                date_joined=joined,
            )
            if classroom:
                classroom.add_member(user)
            return user

        # Full video in March: reached.
        self.full = learner("full.video", FEMALE, self.class_a)
        # Half a video in March: not reached.
        self.half = learner("half.video", MALE, self.class_a)
        # Only teacher-channel completions: not reached.
        self.teacher_ch = learner("teacher.channel", FEMALE, self.class_b)
        # Reached in February: cumulative but not new in March.
        self.feb = learner("feb.reach", MALE, self.class_b)
        # Completes at 23:30 on 31 March in Lusaka (21:30 UTC): March.
        self.edge_in = learner("edge.in", FEMALE, self.class_b)
        # Completes at 00:30 on 1 April in Lusaka (still 31 March UTC): April.
        self.edge_out = learner("edge.out", MALE, self.class_b)
        # Coach (has a role): excluded everywhere.
        self.coach = learner("the.coach", FEMALE, self.class_a)
        self.class_a.add_coach(self.coach)
        # Device superuser with no role: excluded everywhere.
        self.superuser = learner("the.super", MALE, None)
        DevicePermissions.objects.create(user=self.superuser, is_superuser=True)

        self.complete(self.full, lusaka(2026, 3, 10, 9), video_seconds=600)
        self.watch(self.half, lusaka(2026, 3, 11, 9), seconds=300, progress=0.5)
        self.complete(
            self.teacher_ch,
            lusaka(2026, 3, 12, 9),
            channel=TEACHER_CHANNEL,
            video_seconds=900,
        )
        self.complete(self.feb, lusaka(2026, 2, 20, 9))
        self.complete(self.edge_in, lusaka(2026, 3, 31, 23, 30))
        self.complete(self.edge_out, lusaka(2026, 4, 1, 0, 30))
        self.complete(self.coach, lusaka(2026, 3, 10, 9), video_seconds=1000)
        self.complete(self.superuser, lusaka(2026, 3, 10, 9), video_seconds=1000)

        for user in (self.full, self.half, self.coach):
            self.session(user, lusaka(2026, 3, 10, 8))
        self.session(self.full, lusaka(2026, 3, 20, 8))
        self.session(self.half, lusaka(2026, 4, 1, 0, 30))  # April in Lusaka

    # ---------------------------------------------------------------- fixtures

    def watch(self, user, when, seconds, progress, channel=LSHE_CHANNEL):
        content_id = uuid.uuid4().hex
        ContentSessionLog.objects.create(
            user=user,
            content_id=content_id,
            channel_id=channel,
            start_timestamp=when - datetime.timedelta(seconds=seconds),
            end_timestamp=when,
            time_spent=seconds,
            progress=progress,
            kind="video",
        )
        return ContentSummaryLog.objects.create(
            user=user,
            content_id=content_id,
            channel_id=channel,
            start_timestamp=when - datetime.timedelta(seconds=seconds),
            end_timestamp=when,
            completion_timestamp=when if progress >= 1 else None,
            time_spent=seconds,
            progress=progress,
            kind="video",
        )

    def complete(self, user, when, channel=LSHE_CHANNEL, video_seconds=60):
        return self.watch(user, when, video_seconds, 1, channel=channel)

    def session(self, user, when):
        UserSessionLog.objects.create(user=user, start_timestamp=when)

    # ------------------------------------------------------------------ helpers

    def run_report(self, month="2026-03"):
        out = io.StringIO()
        call_command(
            lshereport.Command(),
            "--month",
            month,
            "--output-dir",
            self.out_dir,
            stdout=out,
        )
        return out.getvalue()

    def read_csv(self, month="2026-03"):
        path = os.path.join(self.out_dir, "lshe_TESTCENTRE_{}.csv".format(month))
        with io.open(path, encoding="utf-8") as f:
            text = f.read()
        rows = list(csv.DictReader(io.StringIO(text)))
        return text, {(r["class"], r["gender"]): r for r in rows}

    def figure(self, rows, cls, gender, metric):
        return int(rows[(cls, gender)][metric])

    # -------------------------------------------------------------------- tests

    def test_full_video_reached_half_video_not(self):
        self.run_report()
        _, rows = self.read_csv()
        self.assertEqual(self.figure(rows, "Grade 5 A", FEMALE, "reached_new"), 1)
        self.assertEqual(self.figure(rows, "Grade 5 A", MALE, "reached_new"), 0)
        self.assertEqual(self.figure(rows, "Grade 5 A", MALE, "reached_cumulative"), 0)
        # Half video still counts as watch time, from the session log.
        self.assertEqual(
            self.figure(rows, "Grade 5 A", MALE, "video_watch_seconds"), 300
        )
        self.assertEqual(
            self.figure(rows, "Grade 5 A", FEMALE, "video_watch_seconds"), 600
        )

    def test_coach_and_superuser_excluded(self):
        self.run_report()
        _, rows = self.read_csv()
        # Grade 5 A has the full-video learner, the half-video learner and a coach.
        self.assertEqual(self.figure(rows, "Grade 5 A", ALL, "enrolled_learners"), 2)
        self.assertEqual(self.figure(rows, "Grade 5 A", ALL, "completions"), 1)
        self.assertEqual(
            self.figure(rows, "Grade 5 A", ALL, "video_watch_seconds"), 900
        )
        self.assertEqual(self.figure(rows, CENTRE, ALL, "enrolled_learners"), 6)
        self.assertNotIn(("NO_CLASS", ALL), rows, "the superuser must not appear")

    def test_teacher_channel_excluded(self):
        self.run_report()
        _, rows = self.read_csv()
        self.assertEqual(
            self.figure(rows, "Grade 6 A", FEMALE, "video_watch_seconds"), 60
        )
        # teacher.channel (F) has no LSHE completion; edge.in (F) does.
        self.assertEqual(
            self.figure(rows, "Grade 6 A", FEMALE, "reached_cumulative"), 1
        )

    def test_month_boundaries_use_lusaka_time(self):
        self.run_report()
        _, march = self.read_csv()
        self.assertEqual(
            self.figure(march, "Grade 6 A", FEMALE, "reached_new"), 1
        )  # edge.in
        self.assertEqual(self.figure(march, "Grade 6 A", MALE, "reached_new"), 0)
        self.assertEqual(
            self.figure(march, "Grade 6 A", MALE, "reached_cumulative"), 1
        )  # feb only
        self.run_report("2026-04")
        _, april = self.read_csv("2026-04")
        self.assertEqual(
            self.figure(april, "Grade 6 A", MALE, "reached_new"), 1
        )  # edge.out
        self.assertEqual(self.figure(april, "Grade 6 A", MALE, "reached_cumulative"), 2)
        self.assertEqual(self.figure(april, "Grade 5 A", MALE, "sessions"), 1)

    def test_february_reach_is_cumulative_not_new(self):
        self.run_report()
        _, rows = self.read_csv()
        self.assertEqual(
            self.figure(rows, CENTRE, ALL, "reached_new"), 2
        )  # full, edge.in
        self.assertEqual(
            self.figure(rows, CENTRE, ALL, "reached_cumulative"), 3
        )  # + feb

    def test_sessions_and_active_learners(self):
        self.run_report()
        _, rows = self.read_csv()
        self.assertEqual(self.figure(rows, "Grade 5 A", FEMALE, "sessions"), 2)
        self.assertEqual(self.figure(rows, "Grade 5 A", ALL, "active_learners"), 2)
        self.assertEqual(
            self.figure(rows, "Grade 5 A", ALL, "sessions"), 3
        )  # coach excluded

    def test_learner_in_two_classes_counted_once_in_centre_total(self):
        self.class_b.add_member(self.full)
        self.run_report()
        _, rows = self.read_csv()
        self.assertEqual(self.figure(rows, "Grade 6 A", FEMALE, "reached_new"), 2)
        self.assertEqual(self.figure(rows, CENTRE, ALL, "reached_new"), 2)
        self.assertEqual(self.figure(rows, CENTRE, ALL, "enrolled_learners"), 6)

    def test_no_personal_data_in_output(self):
        self.run_report()
        text, _ = self.read_csv()
        with io.open(os.path.join(self.out_dir, "lshe_TESTCENTRE_2026-03.json")) as f:
            text += f.read()
        for user in FacilityUser.objects.all():
            self.assertNotIn(user.username, text)
            self.assertNotIn(user.full_name, text)
            self.assertNotIn(user.id, text)
        self.assertNotIn("2014", text)

    def test_rerun_is_identical_even_after_class_change(self):
        self.run_report()
        first, _ = self.read_csv()
        # Moving a learner after the month has ended must not change March.
        self.class_a.remove_member(self.full)
        self.class_b.add_member(self.full)
        self.run_report()
        second, _ = self.read_csv()
        self.assertEqual(first, second)
        self.assertTrue(LSHEMonthlyEnrolment.objects.filter(month="2026-03").exists())

    def test_deletefacility_removes_snapshot(self):
        from kolibri.core.auth.utils.delete import delete_facility

        self.run_report()
        self.assertTrue(LSHEMonthlyEnrolment.objects.exists())
        delete_facility(self.facility)
        self.assertFalse(LSHEMonthlyEnrolment.objects.exists())
        self.assertFalse(FacilityUser.objects.exists())

    def test_unfinished_month_not_saved(self):
        now = datetime.datetime.now(LUSAKA)
        month = "{:04d}-{:02d}".format(now.year, now.month)
        out = self.run_report(month)
        self.assertIn("has not finished", out)
        self.assertFalse(LSHEMonthlyEnrolment.objects.filter(month=month).exists())
        with io.open(
            os.path.join(self.out_dir, "lshe_TESTCENTRE_{}.json".format(month))
        ) as f:
            self.assertFalse(json.load(f)["month_complete"])

    def test_metadata(self):
        self.run_report()
        with io.open(os.path.join(self.out_dir, "lshe_TESTCENTRE_2026-03.json")) as f:
            meta = json.load(f)
        self.assertEqual(meta["timezone"], "Africa/Lusaka")
        self.assertEqual(meta["month_start"], "2026-03-01T00:00:00+02:00")
        self.assertEqual(meta["facility_ids"], [self.facility.id])
        self.assertEqual(meta["excluded_teacher_channel_ids"], [TEACHER_CHANNEL])
        self.assertTrue(meta["month_complete"])
        self.assertIn("kolibri_version", meta)

    def test_columns(self):
        self.run_report()
        text, _ = self.read_csv()
        self.assertEqual(text.splitlines()[0], ",".join(lshereport.COLUMNS))
        row = text.splitlines()[1].split(",")
        self.assertEqual(row[:2], ["TESTCENTRE", "2026-03"])

    def test_centre_code_required(self):
        with mock.patch.dict(os.environ, {"KOLIBRI_CENTRE_CODE": ""}):
            with self.assertRaises(CommandError):
                self.run_report()

    def test_bad_month_rejected(self):
        for month in ("2026-13", "March", "2026-3"):
            with self.assertRaises(CommandError):
                self.run_report(month)


ALL = lshereport.ALL
CENTRE = lshereport.CENTRE_TOTAL
