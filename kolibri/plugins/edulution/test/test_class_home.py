"""
The coach's Class home shows which learners are not yet reached (no item
finished) and how far the class has got in each topic of its grade band.
Both come from the class summary. All data here is invented.
"""
import uuid

from django.test import override_settings
from django.urls import reverse
from le_utils.constants import content_kinds
from rest_framework.test import APITestCase

from kolibri.core.auth.models import FacilityUser
from kolibri.core.content.models import ChannelMetadata
from kolibri.core.content.models import ContentNode
from kolibri.core.lessons.models import Lesson
from kolibri.core.logger.models import ContentSummaryLog
from kolibri.plugins.edulution.models import GradeBandChannel
from kolibri.plugins.edulution.test.test_grade_bands import BandFixture
from kolibri.plugins.edulution.test.test_grade_bands import PASSWORD
from kolibri.utils.time_utils import local_now


def node(channel_id, parent, title, kind, tree_id, level, lft, rght):
    return ContentNode.objects.create(
        id=uuid.uuid4().hex,
        channel_id=channel_id,
        content_id=uuid.uuid4().hex,
        parent=parent,
        title=title,
        kind=kind,
        available=True,
        tree_id=tree_id,
        level=level,
        lft=lft,
        rght=rght,
    )


@override_settings(LSHE_GRADE_BANDS="on")
class ClassHomeSummaryTestCase(BandFixture, APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.build()
        cls.learner2 = FacilityUser.objects.create(
            username="grade4.learner2", facility=cls.facility
        )
        cls.lower.add_member(cls.learner2)

        # A band channel with two topics: "Online safety" (two videos)
        # then "Puberty and the body" (one video).
        cls.channel_id = uuid.uuid4().hex
        tree = 9
        root = node(cls.channel_id, None, "LSHE topics", "topic", tree, 0, 1, 12)
        cls.safety = node(cls.channel_id, root, "Online safety", "topic", tree, 1, 2, 7)
        cls.v1 = node(cls.channel_id, cls.safety, "Video 1", "video", tree, 2, 3, 4)
        cls.v2 = node(cls.channel_id, cls.safety, "Video 2", "video", tree, 2, 5, 6)
        cls.puberty = node(
            cls.channel_id, root, "Puberty and the body", "topic", tree, 1, 8, 11
        )
        cls.v3 = node(cls.channel_id, cls.puberty, "Video 3", "video", tree, 2, 9, 10)
        ChannelMetadata.objects.create(
            id=cls.channel_id,
            name="LSHE topics",
            root=root,
            min_schema_version="1",
            version=1,
            order=1,
        )
        GradeBandChannel.objects.create(band="G4-5", channel_id=cls.channel_id)

    def setUp(self):
        self.client.login(
            username=self.coach.username, password=PASSWORD, facility=self.facility
        )

    def log(self, user, content, progress):
        ContentSummaryLog.objects.create(
            user=user,
            content_id=content.content_id,
            channel_id=self.channel_id,
            kind=content_kinds.VIDEO,
            progress=progress,
            start_timestamp=local_now(),
        )

    def summary(self, classroom):
        response = self.client.get(
            reverse(
                "kolibri:kolibri.plugins.edulutionCoach:classsummary-detail",
                kwargs={"pk": classroom.id},
            )
        )
        self.assertEqual(response.status_code, 200)
        return response.data

    def test_reached_learners(self):
        self.log(self.learner, self.v1, 1)
        self.log(self.learner2, self.v3, 0.5)
        data = self.summary(self.lower)
        self.assertEqual(data["reached_learner_ids"], [self.learner.id])

    def test_topic_progress_in_channel_order(self):
        self.log(self.learner, self.v1, 1)
        self.log(self.learner, self.v2, 1)
        self.log(self.learner2, self.v1, 1)
        self.log(self.learner2, self.v3, 0.4)
        Lesson.objects.create(
            title="Puberty 1",
            collection=self.lower,
            created_by=self.coach,
            is_active=True,
            resources=[
                {
                    "contentnode_id": self.v3.id,
                    "content_id": self.v3.content_id,
                    "channel_id": self.channel_id,
                }
            ],
        )
        topics = {t["title"]: t for t in self.summary(self.lower)["band_topics"]}
        self.assertEqual(list(topics), ["Online safety", "Puberty and the body"])
        safety = topics["Online safety"]
        self.assertEqual(
            (safety["completed"], safety["started"], safety["not_started"]), (1, 1, 0)
        )
        self.assertEqual(safety["resource_count"], 2)
        self.assertFalse(safety["in_active_lesson"])
        puberty = topics["Puberty and the body"]
        self.assertEqual(
            (puberty["completed"], puberty["started"], puberty["not_started"]),
            (0, 1, 1),
        )
        self.assertTrue(puberty["in_active_lesson"])

    def test_hidden_lesson_does_not_count_as_taught(self):
        Lesson.objects.create(
            title="Safety 1",
            collection=self.lower,
            created_by=self.coach,
            is_active=False,
            resources=[
                {
                    "contentnode_id": self.v1.id,
                    "content_id": self.v1.content_id,
                    "channel_id": self.channel_id,
                }
            ],
        )
        topics = {t["title"]: t for t in self.summary(self.lower)["band_topics"]}
        self.assertFalse(topics["Online safety"]["in_active_lesson"])

    def test_no_band_no_topics(self):
        self.assertEqual(self.summary(self.unbanded)["band_topics"], [])

    def test_other_band_topics_not_shown(self):
        titles = [t["title"] for t in self.summary(self.upper)["band_topics"]]
        self.assertNotIn("Online safety", titles)

    @override_settings(LSHE_GRADE_BANDS="off")
    def test_no_band_rule_no_topics(self):
        self.assertEqual(self.summary(self.lower)["band_topics"], [])
