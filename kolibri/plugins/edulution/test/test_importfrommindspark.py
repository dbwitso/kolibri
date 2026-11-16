"""
Tests for `kolibri manage importfrommindspark`, against an in-memory MongoDB
(mongomock). All learner data here is invented.
"""
import mock
import mongomock
from bson import ObjectId
from django.core.management import call_command
from django.test import SimpleTestCase
from django.test import TestCase
from six import StringIO

from kolibri.core.auth.constants.demographics import FEMALE
from kolibri.core.auth.constants.demographics import MALE
from kolibri.core.auth.constants.demographics import NOT_SPECIFIED
from kolibri.core.auth.models import Classroom
from kolibri.core.auth.models import Facility
from kolibri.core.auth.models import FacilityUser
from kolibri.core.auth.models import LearnerGroup
from kolibri.core.auth.models import Membership
from kolibri.plugins.edulution.management.commands import importfrommindspark
from kolibri.plugins.edulution.management.commands.importfrommindspark import (
    kolibri_username,
)

MODULE = "kolibri.plugins.edulution.management.commands.importfrommindspark"
URI = "mongodb://placeholder.invalid:27017"

UID_A = ObjectId("650000000000000000000001")  # ObjectId-typed UID
UID_B = "UID-B"  # string-typed UID
UID_STAFF = "UID-STAFF"


class MindSparkUsernameTestCase(SimpleTestCase):
    def test_dots_are_kept(self):
        self.assertEqual(kolibri_username("kalonda.kamona"), "kalonda.kamona")

    def test_other_characters_become_underscores(self):
        self.assertEqual(kolibri_username(" mary-jane o'neil "), "mary_jane_o_neil")

    def test_truncated_to_thirty(self):
        self.assertEqual(len(kolibri_username("x." * 40)), 30)


class ImportFromMindSparkTestCase(TestCase):
    def setUp(self):
        self.facility = Facility.objects.create(name="Centre")
        dataset = self.facility.dataset
        # As the formal preset: passwordless sign-in needs password editing off.
        dataset.learner_can_edit_password = False
        dataset.learner_can_login_with_no_password = True
        dataset.save()

        self.mongo = mongomock.MongoClient()
        self.um = self.mongo["UserManagement"]
        self.auth = self.mongo["UserAuthentication"]
        self.um.UserDetails.insert_many(
            [
                {
                    "UID": UID_A,
                    "firstName": "Kalonda",
                    "lastName": "Kamona",
                    "gender": "Girl",
                    "dateOfBirth": "2014-05-01",
                    "status": "A",
                    "orgID": "ORG1",
                },
                {
                    "UID": UID_B,
                    "name": "Mutale Banda",
                    "gender": "boy",
                    "dateOfBirth": "",
                    "status": "A",
                    "orgID": "ORG1",
                },
                {
                    "UID": UID_STAFF,
                    "name": "Staff Person",
                    "status": "A",
                    "orgID": "ORG1",
                },
            ]
        )
        self.auth.Authentication.insert_many(
            [
                {"UID": UID_A, "username": "kalonda.kamona"},
                {"UID": UID_B, "username": "mutale.banda"},
                {"UID": UID_STAFF, "username": "teacher.one"},
            ]
        )
        self.class_map = {}

        patcher = mock.patch(MODULE + ".MongoClient", return_value=self.mongo)
        patcher.start()
        self.addCleanup(patcher.stop)
        # mongomock has no admin "ping"; the real server check is not under test.
        ping = mock.patch.object(
            mongomock.Database, "command", return_value={"ok": 1}, create=True
        )
        ping.start()
        self.addCleanup(ping.stop)
        class_patcher = mock.patch(
            MODULE + ".build_class_map", side_effect=lambda um: dict(self.class_map)
        )
        class_patcher.start()
        self.addCleanup(class_patcher.stop)

    def run_import(self, *args):
        out = StringIO()
        call_command(
            importfrommindspark.Command(),
            "--mongo-uri",
            URI,
            "--facility",
            self.facility.id,
            *args,
            stdout=out
        )
        return out.getvalue()

    def user(self, uid):
        return FacilityUser.objects.get(facility=self.facility, id_number=str(uid))

    def classes_of(self, user):
        return set(
            Membership.objects.filter(
                user=user, collection__kind="classroom"
            ).values_list("collection__name", flat=True)
        )

    # ---------------------------------------------------------------- create

    def test_create(self):
        out = self.run_import()
        self.assertEqual(FacilityUser.objects.count(), 2)
        a = self.user(UID_A)
        self.assertEqual(a.username, "kalonda.kamona")
        self.assertEqual(a.full_name, "Kalonda Kamona")
        self.assertEqual(a.gender, FEMALE)
        self.assertEqual(a.birth_year, "2014")
        self.assertEqual(a.password, NOT_SPECIFIED)
        b = self.user(UID_B)
        self.assertEqual(b.username, "mutale.banda")
        self.assertEqual(b.gender, MALE)
        self.assertEqual(b.birth_year, NOT_SPECIFIED)
        self.assertFalse(
            FacilityUser.objects.filter(username="teacher.one").exists(),
            "staff accounts must be skipped",
        )
        self.assertIn("created", out)
        self.assertIn("skipped_staff", out)

    def test_rerun_without_changes_is_a_no_op(self):
        self.class_map = {str(UID_A): "Grade 5 A"}
        self.run_import()
        before = {
            u.id: (u.username, u.full_name, u.gender, u.birth_year)
            for u in FacilityUser.objects.all()
        }
        memberships = Membership.objects.count()
        out = self.run_import()
        after = {
            u.id: (u.username, u.full_name, u.gender, u.birth_year)
            for u in FacilityUser.objects.all()
        }
        self.assertEqual(before, after)
        self.assertEqual(Membership.objects.count(), memberships)
        self.assertEqual(Classroom.objects.count(), 1)
        self.assertRegex(out, r"unchanged\s+2")
        self.assertNotIn("created", out)
        self.assertNotIn("updated", out)

    # ---------------------------------------------------------------- update

    def test_update_in_place(self):
        self.run_import()
        pk = self.user(UID_B).pk
        self.um.UserDetails.update_one(
            {"UID": UID_B}, {"$set": {"gender": "F", "dateOfBirth": "2013-01-09"}}
        )
        out = self.run_import()
        b = self.user(UID_B)
        self.assertEqual(b.pk, pk)
        self.assertEqual(b.gender, FEMALE)
        self.assertEqual(b.birth_year, "2013")
        self.assertEqual(FacilityUser.objects.count(), 2)
        self.assertRegex(out, r"updated\s+1")

    def test_name_change(self):
        self.run_import()
        pk = self.user(UID_A).pk
        self.um.UserDetails.update_one({"UID": UID_A}, {"$set": {"lastName": "Mwale"}})
        self.run_import()
        a = self.user(UID_A)
        self.assertEqual(a.pk, pk)
        self.assertEqual(a.full_name, "Kalonda Mwale")

    def test_class_change(self):
        self.class_map = {str(UID_A): "Grade 5 A", UID_B: "Grade 5 A"}
        self.run_import()
        a = self.user(UID_A)
        classroom = Classroom.objects.get(name="Grade 5 A")
        group = LearnerGroup.objects.create(name="Group 1", parent=classroom)
        group.add_member(a)

        self.class_map = {str(UID_A): "Grade 6 B", UID_B: "Grade 5 A"}
        self.run_import()
        self.assertEqual(self.classes_of(a), {"Grade 6 B"})
        self.assertFalse(
            Membership.objects.filter(user=a, collection=group).exists(),
            "leaving a class must also leave its learner groups",
        )
        self.assertEqual(self.classes_of(self.user(UID_B)), {"Grade 5 A"})

    # ----------------------------------------------------------- deactivated

    def _deactivate_a(self):
        self.class_map = {str(UID_A): "Grade 5 A"}
        self.run_import()
        self.um.UserDetails.update_one({"UID": UID_A}, {"$set": {"status": "D"}})

    def test_deactivated_learner_kept_by_default(self):
        self._deactivate_a()
        out = self.run_import()
        a = self.user(UID_A)
        self.assertEqual(self.classes_of(a), {"Grade 5 A"})
        self.assertRegex(out, r"inactive_in_mindspark\s+1")

    def test_deactivated_learner_removed_from_class_with_flag(self):
        self._deactivate_a()
        out = self.run_import("--remove-inactive")
        a = self.user(UID_A)  # the account itself is never deleted
        self.assertEqual(self.classes_of(a), set())
        self.assertRegex(out, r"inactive_removed_from_class\s+1")

    def test_deactivated_learner_not_created(self):
        self.um.UserDetails.update_one({"UID": UID_B}, {"$set": {"status": "D"}})
        self.run_import()
        self.assertFalse(FacilityUser.objects.filter(id_number=UID_B).exists())

    # -------------------------------------------------------------- collision

    def test_username_collision_with_existing_kolibri_user(self):
        other = FacilityUser.objects.create(
            username="kalonda.kamona", facility=self.facility
        )
        out = self.run_import()
        self.assertEqual(self.user(UID_A).username, "kalonda.kamona_2")
        other.refresh_from_db()
        self.assertEqual(other.username, "kalonda.kamona")
        self.assertRegex(out, r"username_changed\s+1")

    def test_username_collision_case_insensitive_within_run(self):
        self.auth.Authentication.update_one(
            {"UID": UID_B}, {"$set": {"username": "Kalonda.Kamona"}}
        )
        self.run_import()
        names = {self.user(UID_A).username.lower(), self.user(UID_B).username.lower()}
        self.assertEqual(len(names), 2)

    def test_collision_suffix_respects_max_length(self):
        long_name = "a" * 25 + ".bcde"  # 30 characters
        FacilityUser.objects.create(username=long_name, facility=self.facility)
        self.auth.Authentication.update_one(
            {"UID": UID_B}, {"$set": {"username": long_name}}
        )
        self.run_import()
        username = self.user(UID_B).username
        self.assertLessEqual(len(username), 30)
        self.assertNotEqual(username.lower(), long_name.lower())

    # ---------------------------------------------------------------- dry run

    def test_dryrun_leaves_database_unchanged(self):
        self.class_map = {str(UID_A): "Grade 5 A"}
        users = FacilityUser.objects.count()
        classes = Classroom.objects.count()
        memberships = Membership.objects.count()
        out = self.run_import("--dryrun")
        self.assertEqual(FacilityUser.objects.count(), users)
        self.assertEqual(Classroom.objects.count(), classes)
        self.assertEqual(Membership.objects.count(), memberships)
        # ... but it still reports what it would have done
        self.assertRegex(out, r"created\s+2")
        self.assertIn("Dry run", out)

    def test_dryrun_leaves_existing_learners_unchanged(self):
        self.run_import()
        self.um.UserDetails.update_one({"UID": UID_A}, {"$set": {"lastName": "X"}})
        self.run_import("--dryrun")
        self.assertEqual(self.user(UID_A).full_name, "Kalonda Kamona")

    # ---------------------------------------------------------------- filters

    def test_org_id_filter(self):
        self.um.UserDetails.update_one({"UID": UID_B}, {"$set": {"orgID": "ORG2"}})
        self.run_import("--org-id", "ORG1")
        self.assertTrue(FacilityUser.objects.filter(id_number=str(UID_A)).exists())
        self.assertFalse(FacilityUser.objects.filter(id_number=UID_B).exists())

    def test_mindspark_is_never_written(self):
        writes = [
            "insert_one",
            "insert_many",
            "update_one",
            "update_many",
            "replace_one",
            "delete_one",
            "delete_many",
            "find_one_and_update",
            "find_one_and_replace",
            "find_one_and_delete",
            "bulk_write",
            "drop",
        ]
        patches = [
            mock.patch.object(
                mongomock.Collection, name, side_effect=AssertionError(name)
            )
            for name in writes
        ]
        for p in patches:
            p.start()
        try:
            self.class_map = {str(UID_A): "Grade 5 A"}
            self.run_import("--remove-inactive")
        finally:
            for p in patches:
                p.stop()
