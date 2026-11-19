"""
A facility admin turns coach quizzes and groups off on the facility's
Settings page; the coach pages read the result. All data here is invented.
"""
from django.urls import reverse
from rest_framework.test import APITestCase

from kolibri.core.auth.models import FacilityUser
from kolibri.plugins.edulution.test.test_grade_bands import BandFixture
from kolibri.plugins.edulution.test.test_grade_bands import PASSWORD
from kolibri.plugins.edulutionCoach.coach_features import coach_features_by_facility
from kolibri.plugins.edulutionCoach.kolibri_plugin import CoachAsset


class CoachFeaturesTestCase(BandFixture, APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.build()
        cls.admin = FacilityUser.objects.create(
            username="centre.admin", facility=cls.facility
        )
        cls.admin.set_password(PASSWORD)
        cls.admin.save()
        cls.facility.add_admin(cls.admin)

    def save_extra(self, user, **values):
        self.client.login(
            username=user.username, password=PASSWORD, facility=self.facility
        )
        dataset = self.facility.dataset
        dataset.refresh_from_db()
        extra = dict(dataset.extra_fields or {}, **values)
        return self.client.patch(
            reverse("kolibri:core:facilitydataset-detail", kwargs={"pk": dataset.id}),
            {"extra_fields": extra},
            format="json",
        )

    def test_on_by_default(self):
        self.assertEqual(
            coach_features_by_facility()[self.facility.id],
            {"quizzes": True, "groups": True},
        )

    def test_admin_turns_them_off(self):
        response = self.save_extra(self.admin, coach_quizzes=False, coach_groups=False)
        self.assertEqual(response.status_code, 200, response.content)
        self.assertEqual(
            coach_features_by_facility()[self.facility.id],
            {"quizzes": False, "groups": False},
        )
        # The PIN and other extra settings are kept.
        self.facility.dataset.refresh_from_db()
        self.assertIn("pin_code", self.facility.dataset.extra_fields)

    def test_admin_turns_one_back_on(self):
        self.save_extra(self.admin, coach_quizzes=False, coach_groups=False)
        self.save_extra(self.admin, coach_groups=True)
        self.assertEqual(
            coach_features_by_facility()[self.facility.id],
            {"quizzes": False, "groups": True},
        )

    def test_coach_cannot_change_them(self):
        response = self.save_extra(self.coach, coach_quizzes=False)
        self.assertIn(response.status_code, (403, 404))
        self.assertTrue(coach_features_by_facility()[self.facility.id]["quizzes"])

    def test_sent_to_the_coach_pages(self):
        self.save_extra(self.admin, coach_quizzes=False)
        data = CoachAsset().plugin_data
        self.assertFalse(data["coach_features"][self.facility.id]["quizzes"])
        self.assertTrue(data["coach_features"][self.facility.id]["groups"])
