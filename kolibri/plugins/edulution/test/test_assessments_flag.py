"""
The learner and coach pages are told whether assessments are switched off
(LSHE_DISABLE_ASSESSMENTS), so they don't call the assessments API, which
then refuses every request. A refused call used to stop the coach's class
summary loading, which broke every Plan and Reports page.
"""
import os

import mock
from django.test import override_settings
from django.test import TestCase

from kolibri.plugins.edulution.kolibri_plugin import EdulutionAsset
from kolibri.plugins.edulutionCoach.kolibri_plugin import CoachAsset


class AssessmentsFlagTestCase(TestCase):
    def flags(self):
        return (
            EdulutionAsset().plugin_data["assessmentsEnabled"],
            CoachAsset().plugin_data["assessments_enabled"],
        )

    def test_on_by_default(self):
        with mock.patch.dict(os.environ):
            os.environ.pop("LSHE_DISABLE_ASSESSMENTS", None)
            self.assertEqual(self.flags(), (True, True))

    def test_off_when_switched_off(self):
        for value in ("true", "1", "yes", "on", "TRUE"):
            with mock.patch.dict(os.environ, {"LSHE_DISABLE_ASSESSMENTS": value}):
                self.assertEqual(self.flags(), (False, False), value)

    def test_on_when_switch_is_false(self):
        for value in ("false", "0", "no", "off", ""):
            with mock.patch.dict(os.environ, {"LSHE_DISABLE_ASSESSMENTS": value}):
                self.assertEqual(self.flags(), (True, True), value)


PATCH_DEVICE_SETTING = (
    "kolibri.plugins.edulution.kolibri_plugin.allow_learner_unassigned_resource_access"
)


class UnassignedContentFlagTestCase(TestCase):
    """
    LSHE learners see only what their lessons assign, so the learner pages
    are told to close the library, bookmarks and topic browsing to them.
    """

    def flag(self, grade_bands):
        with mock.patch.dict(os.environ):
            os.environ.pop("LSHE_GRADE_BANDS", None)
            with override_settings(LSHE_GRADE_BANDS=grade_bands):
                return EdulutionAsset().plugin_data[
                    "allowLearnerUnassignedResourceAccess"
                ]

    @mock.patch(PATCH_DEVICE_SETTING, return_value=True)
    def test_closed_with_grade_bands(self, _):
        self.assertIs(self.flag("on"), False)

    @mock.patch(PATCH_DEVICE_SETTING, return_value=True)
    def test_device_setting_without_grade_bands(self, _):
        self.assertIs(self.flag("off"), True)

    @mock.patch(PATCH_DEVICE_SETTING, return_value=False)
    def test_device_setting_off(self, _):
        self.assertIs(self.flag("off"), False)
