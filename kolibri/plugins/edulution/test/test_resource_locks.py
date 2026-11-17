"""
Lesson resource locks (a coach's Lock switch, and the lock set when a
learner completes a resource) must hold however the learner opens the
resource: the learner pages start a session without the lesson id, so the
lock is checked from the learner's lessons too. All data here is invented.
"""
import uuid

from django.test import override_settings
from django.urls import reverse
from rest_framework.test import APITestCase

from kolibri.core.lessons.models import LearnerResourceLock
from kolibri.core.lessons.models import Lesson
from kolibri.core.lessons.models import LessonAssignment
from kolibri.plugins.edulution.test.test_grade_bands import BandFixture
from kolibri.plugins.edulution.test.test_grade_bands import PASSWORD


@override_settings(LSHE_GRADE_BANDS="on")
class ResourceLockTestCase(BandFixture, APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.build()
        cls.learner.set_password(PASSWORD)
        cls.learner.save()

    def setUp(self):
        self.assertTrue(
            self.client.login(
                username=self.learner.username,
                password=PASSWORD,
                facility=self.facility,
            )
        )

    def lesson(self, locked=False, active=True):
        lesson = Lesson.objects.create(
            title="Lesson {}".format(uuid.uuid4().hex[:6]),
            collection=self.lower,
            created_by=self.coach,
            is_active=active,
            resources=[
                {
                    "contentnode_id": self.g45_video.id,
                    "content_id": uuid.uuid4().hex,
                    "channel_id": self.g45_channel,
                    "locked": locked,
                }
            ],
        )
        LessonAssignment.objects.create(
            lesson=lesson, collection=self.lower, assigned_by=self.coach
        )
        return lesson

    def start(self, lesson=None):
        data = {
            "node_id": self.g45_video.id,
            "content_id": uuid.uuid4().hex,
            "channel_id": self.g45_channel,
            "kind": "video",
        }
        if lesson is not None:
            data["lesson_id"] = lesson.id
        return self.client.post(
            reverse("kolibri:core:trackprogress-list"), data, format="json"
        )

    def test_open_resource_starts(self):
        lesson = self.lesson()
        self.assertEqual(self.start().status_code, 200)
        self.assertEqual(self.start(lesson).status_code, 200)

    def test_coach_lock_holds_without_lesson_id(self):
        lesson = self.lesson(locked=True)
        self.assertEqual(self.start(lesson).status_code, 403)
        response = self.start()
        self.assertEqual(response.status_code, 403)

    def test_completion_lock_holds_without_lesson_id(self):
        lesson = self.lesson()
        LearnerResourceLock.objects.create(
            lesson=lesson, user=self.learner, contentnode_id=self.g45_video.id
        )
        self.assertEqual(self.start(lesson).status_code, 403)
        response = self.start()
        self.assertEqual(response.status_code, 403)

    def test_open_in_another_lesson(self):
        self.lesson(locked=True)
        self.lesson(locked=False)
        self.assertEqual(self.start().status_code, 200)

    def test_hidden_lesson_lock_does_not_count(self):
        # A locked copy in a hidden lesson does not block an open one.
        self.lesson(locked=True, active=False)
        self.lesson(locked=False)
        self.assertEqual(self.start().status_code, 200)

    def test_coach_not_blocked(self):
        self.lesson(locked=True)
        self.client.logout()
        self.client.login(
            username=self.coach.username, password=PASSWORD, facility=self.facility
        )
        self.assertEqual(self.start().status_code, 200)


@override_settings(LSHE_GRADE_BANDS="on")
class UnlockLearnerResourceTestCase(BandFixture, APITestCase):
    """The coach's Unlock button in the learner's lesson report."""

    @classmethod
    def setUpTestData(cls):
        cls.build()

    def test_coach_unlocks(self):
        lesson = Lesson.objects.create(
            title="Lesson",
            collection=self.lower,
            created_by=self.coach,
            is_active=True,
            resources=[],
        )
        LearnerResourceLock.objects.create(
            lesson=lesson, user=self.learner, contentnode_id=self.g45_video.id
        )
        self.client.login(
            username=self.coach.username, password=PASSWORD, facility=self.facility
        )
        response = self.client.patch(
            reverse(
                "kolibri:core:lesson-unlock-learner-resource", kwargs={"pk": lesson.id}
            ),
            {"user_id": self.learner.id, "contentnode_id": self.g45_video.id},
            format="json",
        )
        self.assertEqual(response.status_code, 200, response.content)
        self.assertFalse(LearnerResourceLock.objects.exists())

    def test_learner_cannot_unlock(self):
        lesson = Lesson.objects.create(
            title="Lesson",
            collection=self.lower,
            created_by=self.coach,
            is_active=True,
            resources=[],
        )
        LearnerResourceLock.objects.create(
            lesson=lesson, user=self.learner, contentnode_id=self.g45_video.id
        )
        self.learner.set_password(PASSWORD)
        self.learner.save()
        self.client.login(
            username=self.learner.username, password=PASSWORD, facility=self.facility
        )
        response = self.client.patch(
            reverse(
                "kolibri:core:lesson-unlock-learner-resource", kwargs={"pk": lesson.id}
            ),
            {"user_id": self.learner.id, "contentnode_id": self.g45_video.id},
            format="json",
        )
        self.assertIn(response.status_code, (403, 404))
        self.assertTrue(LearnerResourceLock.objects.exists())


@override_settings(LSHE_GRADE_BANDS="on")
class CompletionLockTestCase(ResourceLockTestCase):
    """Finishing a resource locks it, as the learner player opens it."""

    def finish(self, lesson=None):
        response = self.start(lesson)
        self.assertEqual(response.status_code, 200)
        update = self.client.put(
            reverse(
                "kolibri:core:trackprogress-detail",
                kwargs={"pk": response.data["session_id"]},
            ),
            {"progress_delta": 1, "time_spent_delta": 200},
            format="json",
        )
        self.assertEqual(update.status_code, 200)

    def test_locks_without_lesson_id(self):
        lesson = self.lesson()
        hidden = self.lesson(active=False)
        self.finish()
        self.assertTrue(
            LearnerResourceLock.objects.filter(
                lesson=lesson, user=self.learner
            ).exists()
        )
        self.assertFalse(LearnerResourceLock.objects.filter(lesson=hidden).exists())
        self.assertEqual(self.start().status_code, 403)

    def test_locks_with_lesson_id(self):
        lesson = self.lesson()
        self.finish(lesson)
        self.assertEqual(LearnerResourceLock.objects.get().lesson_id, lesson.id)
