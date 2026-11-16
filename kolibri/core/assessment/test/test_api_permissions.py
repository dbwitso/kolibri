"""
Every /api/assessments/ endpoint must refuse signed-out users, refuse people
outside the class or learner concerned, and refuse everyone when assessments
are switched off (LSHE_DISABLE_ASSESSMENTS).

These tests only check access (403 or not). What each endpoint then does with
an allowed request is outside their scope.
"""
import os

import mock
from rest_framework.test import APITestCase

from .. import models
from kolibri.core.auth.models import Classroom
from kolibri.core.auth.models import Facility
from kolibri.core.auth.models import FacilityUser
from kolibri.core.auth.test.helpers import provision_device

BASE = "/api/assessments/"
PASSWORD = "password"


class AssessmentAPIPermissionsTestCase(APITestCase):
    @classmethod
    def setUpTestData(cls):
        provision_device()
        cls.facility = Facility.objects.create(name="Centre")
        cls.class_a = Classroom.objects.create(name="Grade 5 A", parent=cls.facility)
        cls.class_b = Classroom.objects.create(name="Grade 6 A", parent=cls.facility)

        def user(username):
            u = FacilityUser.objects.create(username=username, facility=cls.facility)
            u.set_password(PASSWORD)
            u.save()
            return u

        cls.learner_a = user("learner.a")
        cls.class_a.add_member(cls.learner_a)
        cls.learner_b = user("learner.b")
        cls.class_b.add_member(cls.learner_b)
        cls.coach_a = user("coach.a")
        cls.class_a.add_coach(cls.coach_a)
        cls.coach_b = user("coach.b")
        cls.class_b.add_coach(cls.coach_b)
        cls.admin = user("the.admin")
        cls.facility.add_admin(cls.admin)

        cls.group = models.ExamAssessmentGroup.objects.create(
            title="Group", learner_id=cls.learner_a.id, collection=cls.class_a
        )
        cls.assessment = models.ExamAssessment.objects.create(
            title="Assessment",
            question_count=1,
            collection=cls.class_a,
            learner=cls.learner_a,
            creator=cls.coach_a,
            assessment_group=cls.group,
        )

    # ------------------------------------------------------------- endpoints

    def coach_requests(self):
        """(method, url, data) for coach-only endpoints about class A."""
        a = self.assessment.id
        return [
            ("post", BASE + "assessment/", {"collection": self.class_a.id}),
            ("get", BASE + "assessmentgroup/{}/".format(self.class_a.id), None),
            ("patch", BASE + "assessmentstart/{}/".format(self.group.id), {}),
            ("patch", BASE + "assessmentstop/{}/".format(self.group.id), {}),
            ("get", BASE + "fetchbyassessmentgroupid/{}/".format(self.group.id), None),
            ("post", BASE + "assessmenttest/", {"assessment_id": a, "flag": 1}),
            ("get", BASE + "assessmentpastreport/{}/".format(a), None),
        ]

    def learner_requests(self):
        """(method, url, data) for endpoints about learner A."""
        la = self.learner_a.id
        return [
            ("get", BASE + "learnerassessments/?learner_id={}".format(la), None),
            ("get", BASE + "getassessment/{}/".format(la), None),
            (
                "get",
                BASE + "assessmenthistoryreport/x/?learner_ids={}".format(la),
                None,
            ),
            (
                "post",
                BASE + "markassessment/",
                {
                    "assessment_id": self.assessment.id,
                    "assessment_group_id": self.group.id,
                },
            ),
        ]

    def call(self, method, url, data):
        return getattr(self.client, method)(url, data or {}, format="json")

    def login(self, user):
        self.client.logout()
        if user is not None:
            self.client.login(
                username=user.username, password=PASSWORD, facility=self.facility
            )

    def assertAccess(self, user, requests, allowed):
        self.login(user)
        for method, url, data in requests:
            response = self.call(method, url, data)
            who = user.username if user else "anonymous"
            if allowed:
                self.assertNotEqual(
                    response.status_code,
                    403,
                    "{} refused {} {}".format(who, method, url),
                )
            else:
                self.assertIn(
                    response.status_code,
                    (401, 403),
                    "{} allowed {} {} ({})".format(
                        who, method, url, response.status_code
                    ),
                )

    # ----------------------------------------------------------------- tests

    def test_anonymous_refused_everywhere(self):
        everything = self.coach_requests() + self.learner_requests()
        everything.append(("get", BASE + "assessmentchannels/", None))
        self.assertAccess(None, everything, allowed=False)

    def test_coach_endpoints(self):
        self.assertAccess(self.coach_a, self.coach_requests(), allowed=True)
        self.assertAccess(self.admin, self.coach_requests(), allowed=True)
        self.assertAccess(self.coach_b, self.coach_requests(), allowed=False)
        self.assertAccess(self.learner_a, self.coach_requests(), allowed=False)

    def test_learner_endpoints(self):
        self.assertAccess(self.learner_a, self.learner_requests(), allowed=True)
        self.assertAccess(self.coach_a, self.learner_requests(), allowed=True)
        self.assertAccess(self.learner_b, self.learner_requests(), allowed=False)
        self.assertAccess(self.coach_b, self.learner_requests(), allowed=False)

    def test_channels_list_needs_a_coach(self):
        channels = [("get", BASE + "assessmentchannels/", None)]
        self.assertAccess(self.coach_b, channels, allowed=True)
        self.assertAccess(self.learner_a, channels, allowed=False)

    def test_malformed_ids_refused_not_crashing(self):
        self.login(self.coach_a)
        for url in (
            BASE + "assessmentgroup/not-a-uuid/",
            BASE + "assessmentpastreport/not-a-uuid/",
            BASE + "learnerassessments/?learner_id=not-a-uuid",
        ):
            self.assertEqual(self.client.get(url).status_code, 403, url)

    def test_switched_off_refuses_everyone(self):
        everything = self.coach_requests() + self.learner_requests()
        everything.append(("get", BASE + "assessmentchannels/", None))
        everything.append(("get", BASE + "assessmentdetails/", None))
        with mock.patch.dict(os.environ, {"LSHE_DISABLE_ASSESSMENTS": "true"}):
            self.assertAccess(self.admin, everything, allowed=False)
            self.assertAccess(self.coach_a, everything, allowed=False)
            self.assertAccess(self.learner_a, everything, allowed=False)
