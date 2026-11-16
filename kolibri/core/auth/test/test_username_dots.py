"""
Usernames may contain dots so MindSpark learners keep their exact usernames
(e.g. "kalonda.kamona"). Everything else the validator rejected is still
rejected, and the 30-character limit is unchanged.
"""
from django.core.exceptions import ValidationError
from django.test import TestCase

from kolibri.core.auth.management.commands.bulkimportusers import valid_name
from kolibri.core.auth.models import Facility
from kolibri.core.auth.models import FacilityUser


class UsernameDotsModelTestCase(TestCase):
    def setUp(self):
        self.facility = Facility.objects.create(name="Centre")

    def _user(self, username):
        return FacilityUser(
            username=username, facility=self.facility, password="NOT_SPECIFIED"
        )

    def test_username_with_dot_passes_model_validation(self):
        user = self._user("kalonda.kamona")
        user.full_clean()
        user.save()
        self.assertEqual(
            FacilityUser.objects.get(username="kalonda.kamona").pk, user.pk
        )

    def test_other_punctuation_still_rejected(self):
        for username in ("kalonda kamona", "kalonda-kamona", "kalonda@x", "a,b", "a?b"):
            with self.assertRaises(ValidationError, msg=username):
                self._user(username).full_clean()

    def test_thirty_character_limit_kept(self):
        self._user("a" * 14 + "." + "b" * 15).full_clean()  # 30 characters
        with self.assertRaises(ValidationError):
            self._user("a" * 15 + "." + "b" * 15).full_clean()  # 31 characters


class UsernameDotsBulkImportTestCase(TestCase):
    def test_bulkimport_accepts_dot_in_username(self):
        # valid_name returns a checker that raises ValueError on bad values
        valid_name(username=True)("kalonda.kamona")
        with self.assertRaises(ValueError):
            valid_name(username=True)("kalonda-kamona")
