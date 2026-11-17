"""
LSHE grade bands: coaches can only assign content from their class's band
channels (lessons and quizzes, create and update), classes with no band can
receive nothing, and a learner never sees out-of-band content even when a
bad assignment exists. All data here is invented.
"""
import uuid

from django.test import override_settings
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APITestCase

from kolibri.core import error_constants
from kolibri.core.auth.models import Classroom
from kolibri.core.auth.models import Facility
from kolibri.core.auth.models import FacilityUser
from kolibri.core.auth.models import LearnerGroup
from kolibri.core.auth.test.helpers import provision_device
from kolibri.core.content.models import ChannelMetadata
from kolibri.core.content.models import ContentNode
from kolibri.core.content.utils.learner_visibility import get_assigned_content_ids
from kolibri.core.exams.models import Exam
from kolibri.core.exams.models import ExamAssignment
from kolibri.core.lessons.models import Lesson
from kolibri.core.lessons.models import LessonAssignment
from kolibri.plugins.edulution.models import ClassroomBand
from kolibri.plugins.edulution.models import GradeBandChannel

PASSWORD = "password"


def make_channel(name, tree_id):
    """A channel with a root topic, one video and one exercise."""
    channel_id = uuid.uuid4().hex
    root = ContentNode.objects.create(
        id=uuid.uuid4().hex,
        channel_id=channel_id,
        content_id=uuid.uuid4().hex,
        parent=None,
        title=name,
        kind="topic",
        available=True,
        tree_id=tree_id,
        level=0,
        lft=1,
        rght=6,
    )
    video = ContentNode.objects.create(
        id=uuid.uuid4().hex,
        channel_id=channel_id,
        content_id=uuid.uuid4().hex,
        parent=root,
        title=name + " video",
        kind="video",
        available=True,
        tree_id=tree_id,
        level=1,
        lft=2,
        rght=3,
    )
    exercise = ContentNode.objects.create(
        id=uuid.uuid4().hex,
        channel_id=channel_id,
        content_id=uuid.uuid4().hex,
        parent=root,
        title=name + " exercise",
        kind="exercise",
        available=True,
        tree_id=tree_id,
        level=1,
        lft=4,
        rght=5,
    )
    ChannelMetadata.objects.create(
        id=channel_id, name=name, root=root, min_schema_version="1", version=1
    )
    return channel_id, root, video, exercise


class BandFixture(object):
    @classmethod
    def build(cls):
        provision_device()
        cls.facility = Facility.objects.create(name="Centre")
        cls.lower = Classroom.objects.create(name="Grade 4 A", parent=cls.facility)
        cls.upper = Classroom.objects.create(name="Grade 6 A", parent=cls.facility)
        cls.unbanded = Classroom.objects.create(name="Grade 5 B", parent=cls.facility)
        cls.lower_group = LearnerGroup.objects.create(name="Group 1", parent=cls.lower)

        cls.coach = FacilityUser.objects.create(
            username="the.coach", facility=cls.facility
        )
        cls.coach.set_password(PASSWORD)
        cls.coach.save()
        cls.facility.add_coach(cls.coach)

        cls.learner = FacilityUser.objects.create(
            username="grade4.learner", facility=cls.facility
        )
        cls.lower.add_member(cls.learner)
        cls.lower_group.add_member(cls.learner)

        cls.g45_channel, cls.g45_root, cls.g45_video, cls.g45_exercise = make_channel(
            "LSHE G4-5", 1
        )
        cls.g67_channel, cls.g67_root, cls.g67_video, cls.g67_exercise = make_channel(
            "LSHE G6-7", 2
        )
        GradeBandChannel.objects.create(band="G4-5", channel_id=cls.g45_channel)
        GradeBandChannel.objects.create(band="G6-7", channel_id=cls.g67_channel)
        ClassroomBand.objects.create(classroom=cls.lower, band="G4-5")
        ClassroomBand.objects.create(classroom=cls.upper, band="G6-7")


@override_settings(LSHE_GRADE_BANDS="on")
class GradeBandAssignmentAPITestCase(BandFixture, APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.build()

    def setUp(self):
        self.client.login(
            username=self.coach.username, password=PASSWORD, facility=self.facility
        )

    # ---------------------------------------------------------------- lessons

    def lesson(self, classroom, nodes, assignments=None, **extra):
        data = {
            "title": "Lesson {}".format(uuid.uuid4().hex[:6]),
            "collection": classroom.id,
            "lesson_assignments": [c.id for c in (assignments or [classroom])],
            "resources": [
                {
                    "contentnode_id": n.id,
                    "channel_id": n.channel_id,
                    "content_id": n.content_id,
                }
                for n in nodes
            ],
            "is_active": True,
        }
        data.update(extra)
        return data

    def post_lesson(self, data):
        return self.client.post(
            reverse("kolibri:core:lesson-list"), data, format="json"
        )

    def patch_lesson(self, lesson_id, data):
        return self.client.patch(
            reverse("kolibri:core:lesson-detail", kwargs={"pk": lesson_id}),
            data,
            format="json",
        )

    def assertBandError(self, response):
        self.assertEqual(response.status_code, 400, response.data)
        self.assertEqual(response.data[0]["id"], error_constants.GRADE_BAND_NOT_ALLOWED)
        return response.data[0]["metadata"]["message"]

    def test_in_band_lesson_succeeds(self):
        response = self.post_lesson(self.lesson(self.lower, [self.g45_video]))
        self.assertEqual(response.status_code, 201, response.data)

    def test_in_band_lesson_to_learner_group_succeeds(self):
        response = self.post_lesson(
            self.lesson(self.lower, [self.g45_video], assignments=[self.lower_group])
        )
        self.assertEqual(response.status_code, 201, response.data)

    def test_out_of_band_lesson_rejected(self):
        response = self.post_lesson(
            self.lesson(self.lower, [self.g45_video, self.g67_video])
        )
        message = self.assertBandError(response)
        self.assertIn("Grade 4 A", message)
        self.assertIn("G4-5", message)
        self.assertIn("LSHE G6-7 video", message)
        self.assertFalse(Lesson.objects.exists())

    def test_out_of_band_lesson_to_learner_group_rejected(self):
        response = self.post_lesson(
            self.lesson(self.lower, [self.g67_video], assignments=[self.lower_group])
        )
        self.assertBandError(response)

    def test_unbanded_class_rejected(self):
        response = self.post_lesson(self.lesson(self.unbanded, [self.g45_video]))
        message = self.assertBandError(response)
        self.assertIn("no grade band", message)

    def test_update_adding_out_of_band_resource_rejected(self):
        response = self.post_lesson(self.lesson(self.lower, [self.g45_video]))
        lesson_id = response.data["id"]
        resources = self.lesson(self.lower, [self.g45_video, self.g67_video])[
            "resources"
        ]
        self.assertBandError(self.patch_lesson(lesson_id, {"resources": resources}))
        self.assertEqual(len(Lesson.objects.get(id=lesson_id).resources), 1)

    def test_update_assigning_to_other_band_class_rejected(self):
        # A G4-5 lesson cannot be re-assigned into a G6-7 class's group either.
        upper_group = LearnerGroup.objects.create(name="Group U", parent=self.upper)
        response = self.post_lesson(self.lesson(self.lower, [self.g45_video]))
        self.assertBandError(
            self.patch_lesson(
                response.data["id"], {"lesson_assignments": [upper_group.id]}
            )
        )

    def test_bad_lesson_can_still_be_deactivated(self):
        lesson = Lesson.objects.create(
            title="Old",
            collection=self.lower,
            created_by=self.coach,
            is_active=True,
            resources=self.lesson(self.lower, [self.g67_video])["resources"],
        )
        response = self.patch_lesson(lesson.id, {"is_active": False})
        self.assertEqual(response.status_code, 200, response.data)
        lesson.refresh_from_db()
        self.assertFalse(lesson.is_active)
        # ...but it cannot be switched back on.
        self.assertBandError(self.patch_lesson(lesson.id, {"is_active": True}))

    def test_whole_facility_assignment_rejected(self):
        response = self.post_lesson(
            self.lesson(self.lower, [self.g45_video], assignments=[self.facility])
        )
        message = self.assertBandError(response)
        self.assertIn("whole facility", message)

    def test_unknown_content_rejected(self):
        data = self.lesson(self.lower, [self.g45_video])
        data["resources"][0]["contentnode_id"] = uuid.uuid4().hex
        self.assertBandError(self.post_lesson(data))

    # ---------------------------------------------------------------- quizzes

    def quiz(self, classroom, exercises, assignments=None):
        return {
            "title": "Quiz {}".format(uuid.uuid4().hex[:6]),
            "question_count": len(exercises),
            "active": True,
            "collection": classroom.id,
            "learners_see_fixed_order": False,
            "question_sources": [
                {
                    "exercise_id": e.id,
                    "question_id": uuid.uuid4().hex,
                    "title": e.title,
                    "counter_in_exercise": 1,
                }
                for e in exercises
            ],
            "assignments": [c.id for c in (assignments or [classroom])],
            "date_activated": None,
            "date_archived": None,
        }

    def post_quiz(self, data):
        return self.client.post(reverse("kolibri:core:exam-list"), data, format="json")

    def test_in_band_quiz_succeeds(self):
        response = self.post_quiz(self.quiz(self.upper, [self.g67_exercise]))
        self.assertEqual(response.status_code, 201, response.data)

    def test_out_of_band_quiz_rejected(self):
        response = self.post_quiz(self.quiz(self.lower, [self.g67_exercise]))
        self.assertBandError(response)
        self.assertFalse(Exam.objects.exists())

    def test_quiz_update_adding_out_of_band_exercise_rejected(self):
        response = self.post_quiz(self.quiz(self.lower, [self.g45_exercise]))
        sources = self.quiz(self.lower, [self.g45_exercise, self.g67_exercise])[
            "question_sources"
        ]
        update = self.client.patch(
            reverse("kolibri:core:exam-detail", kwargs={"pk": response.data["id"]}),
            {"question_sources": sources},
            format="json",
        )
        self.assertBandError(update)

    def test_off_switch(self):
        with override_settings(LSHE_GRADE_BANDS="off"):
            response = self.post_lesson(self.lesson(self.unbanded, [self.g67_video]))
        self.assertEqual(response.status_code, 201, response.data)


@override_settings(LSHE_GRADE_BANDS="on")
class GradeBandLearnerVisibilityTestCase(BandFixture, TestCase):
    """The second safeguard: even a bad assignment never shows out-of-band content."""

    @classmethod
    def setUpTestData(cls):
        cls.build()
        resources = [
            {
                "contentnode_id": n.id,
                "channel_id": n.channel_id,
                "content_id": n.content_id,
            }
            for n in (cls.g45_video, cls.g67_video)
        ]
        # Written straight to the database, bypassing the API check, as a
        # stand-in for an assignment made before bands were set up.
        lesson = Lesson.objects.create(
            title="Bad lesson",
            collection=cls.lower,
            created_by=cls.coach,
            is_active=True,
            resources=resources,
        )
        LessonAssignment.objects.create(
            lesson=lesson, collection=cls.lower, assigned_by=cls.coach
        )
        exam = Exam.objects.create(
            title="Bad quiz",
            question_count=2,
            collection=cls.lower,
            creator=cls.coach,
            active=True,
            question_sources=[
                {
                    "exercise_id": e.id,
                    "question_id": uuid.uuid4().hex,
                    "title": e.title,
                    "counter_in_exercise": 1,
                }
                for e in (cls.g45_exercise, cls.g67_exercise)
            ],
        )
        ExamAssignment.objects.create(
            exam=exam, collection=cls.lower, assigned_by=cls.coach
        )

    def test_learner_never_sees_out_of_band_content(self):
        visible = get_assigned_content_ids(self.learner)
        self.assertIn(self.g45_video.id, visible)
        self.assertIn(self.g45_exercise.id, visible)
        self.assertIn(self.g45_root.id, visible)
        self.assertNotIn(self.g67_video.id, visible)
        self.assertNotIn(self.g67_exercise.id, visible)
        self.assertNotIn(self.g67_root.id, visible, "out-of-band topics must not show")

    def test_learner_in_unbanded_class_sees_nothing(self):
        other = FacilityUser.objects.create(
            username="unbanded.learner", facility=self.facility
        )
        self.unbanded.add_member(other)
        lesson = Lesson.objects.get(title="Bad lesson")
        LessonAssignment.objects.create(
            lesson=lesson, collection=self.unbanded, assigned_by=self.coach
        )
        self.assertEqual(get_assigned_content_ids(other), set())

    def test_content_api_hides_out_of_band_nodes(self):
        from rest_framework.test import APIClient

        self.learner.set_password(PASSWORD)
        self.learner.save()
        client = APIClient()
        client.login(
            username=self.learner.username, password=PASSWORD, facility=self.facility
        )
        for node in (self.g67_video, self.g67_root):
            response = client.get(
                reverse("kolibri:core:contentnode-detail", kwargs={"pk": node.id})
            )
            self.assertEqual(response.status_code, 404, node.title)
        response = client.get(
            reverse("kolibri:core:contentnode-detail", kwargs={"pk": self.g45_video.id})
        )
        self.assertEqual(response.status_code, 200)


@override_settings(LSHE_GRADE_BANDS="on")
class RestrictedLearnerCacheTestCase(BandFixture, APITestCase):
    """
    Cached content lists follow what a learner may see: a lesson assigned
    after the learner opened the library shows at once, and the browser's
    ETag no longer matches.
    """

    @classmethod
    def setUpTestData(cls):
        cls.build()
        cls.learner.set_password(PASSWORD)
        cls.learner.save()

    def setUp(self):
        from django.core.cache import cache

        cache.clear()
        self.client.login(
            username=self.learner.username, password=PASSWORD, facility=self.facility
        )
        self.url = reverse("kolibri:core:channel-list")

    def channel_ids(self, response):
        self.assertEqual(response.status_code, 200)
        return {c["id"] for c in response.json()}

    def test_new_lesson_shows_despite_cache(self):
        before = self.client.get(self.url)
        self.assertEqual(self.channel_ids(before), set())
        lesson = Lesson.objects.create(
            title="Friendship",
            collection=self.lower,
            created_by=self.coach,
            is_active=True,
            resources=[
                {
                    "contentnode_id": self.g45_video.id,
                    "channel_id": self.g45_video.channel_id,
                    "content_id": self.g45_video.content_id,
                }
            ],
        )
        LessonAssignment.objects.create(
            lesson=lesson, collection=self.lower, assigned_by=self.coach
        )

        after = self.client.get(self.url)
        self.assertEqual(self.channel_ids(after), {self.g45_channel})
        self.assertNotEqual(before["ETag"], after["ETag"])
        # The browser's copy from before the lesson must not be reused.
        revalidated = self.client.get(self.url, HTTP_IF_NONE_MATCH=before["ETag"])
        self.assertEqual(self.channel_ids(revalidated), {self.g45_channel})

        lesson.is_active = False
        lesson.save()
        self.assertEqual(self.channel_ids(self.client.get(self.url)), set())

    def test_unchanged_visibility_still_revalidates(self):
        first = self.client.get(self.url)
        again = self.client.get(self.url, HTTP_IF_NONE_MATCH=first["ETag"])
        self.assertEqual(again.status_code, 304)
