"""
What learners, signed-out users, teachers and admins can reach through the
content APIs on an LSHE server (grade bands on, so the lockdown is on).

- A Grade 4 learner never gets Grade 6-7 or teacher-channel content (or its
  file checksums, which are its URLs) from any content endpoint.
- Signed-out users get no content at all, and the public content API is off.
- Teachers (classroom coaches) and admins see the teacher channel.
- A teacher sees only their own class.

All data here is invented.
"""
import uuid

from django.test import override_settings
from django.test import TestCase
from rest_framework.test import APIClient

from kolibri.core.auth.constants import role_kinds
from kolibri.core.auth.models import FacilityUser
from kolibri.core.content.models import ChannelMetadata
from kolibri.core.content.models import ContentNode
from kolibri.core.content.models import File
from kolibri.core.content.models import LocalFile
from kolibri.core.lessons.models import Lesson
from kolibri.core.lessons.models import LessonAssignment
from kolibri.plugins.edulution.models import GradeBandChannel
from kolibri.plugins.edulution.test.test_grade_bands import BandFixture
from kolibri.plugins.edulution.test.test_grade_bands import make_channel
from kolibri.plugins.edulution.test.test_grade_bands import PASSWORD

TEACHER_CHANNEL = uuid.uuid4().hex


def add_file(node):
    checksum = uuid.uuid4().hex
    local = LocalFile.objects.create(
        id=checksum, extension="mp4", available=True, file_size=10
    )
    File.objects.create(
        id=uuid.uuid4().hex, contentnode=node, local_file=local, preset="high_res_video"
    )
    return checksum


@override_settings(LSHE_GRADE_BANDS="on", LSHE_TEACHER_CHANNEL_IDS=TEACHER_CHANNEL)
class ContentLockdownTestCase(BandFixture, TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.build()
        # The teacher channel, with a known id.
        _, cls.t_root, cls.t_video, _ = make_channel("Teacher CSE course", 3)
        old = cls.t_root.channel_id
        ContentNode.objects.filter(channel_id=old).update(channel_id=TEACHER_CHANNEL)
        ChannelMetadata.objects.filter(id=old).update(id=TEACHER_CHANNEL)
        cls.t_video.refresh_from_db()

        cls.g45_checksum = add_file(cls.g45_video)
        cls.g67_checksum = add_file(cls.g67_video)
        cls.t_checksum = add_file(cls.t_video)

        lesson = Lesson.objects.create(
            title="In band",
            collection=cls.lower,
            created_by=cls.coach,
            is_active=True,
            resources=[
                {
                    "contentnode_id": cls.g45_video.id,
                    "channel_id": cls.g45_channel,
                    "content_id": cls.g45_video.content_id,
                }
            ],
        )
        LessonAssignment.objects.create(
            lesson=lesson, collection=cls.lower, assigned_by=cls.coach
        )

        cls.learner.set_password(PASSWORD)
        cls.learner.save()

        # A teacher: assignable coach at facility level, coach of Grade 4 A only.
        cls.teacher = FacilityUser.objects.create(
            username="teacher.one", facility=cls.facility
        )
        cls.teacher.set_password(PASSWORD)
        cls.teacher.save()
        cls.facility.add_role(cls.teacher, role_kinds.ASSIGNABLE_COACH)
        cls.lower.add_coach(cls.teacher)

        cls.admin = FacilityUser.objects.create(
            username="the.admin", facility=cls.facility
        )
        cls.admin.set_password(PASSWORD)
        cls.admin.save()
        cls.facility.add_admin(cls.admin)

    def client_for(self, user):
        client = APIClient()
        if user is not None:
            self.assertTrue(
                client.login(
                    username=user.username, password=PASSWORD, facility=self.facility
                )
            )
        return client

    def content_urls(self, node, root, channel):
        return [
            "/api/content/contentnode/{}/".format(node.id),
            "/api/content/contentnode/?channel_id={}".format(channel),
            "/api/content/contentnode/?parent={}".format(root.id),
            "/api/content/usercontentnode/{}/".format(node.id),
            "/api/content/contentnode_tree/{}/".format(root.id),
            "/api/content/contentnode_search/?search=video",
            "/api/content/file/",
            "/api/content/knowledgemap/{}/".format(root.id),
            "/api/content/channel/",
            "/api/content/channel/{}/".format(channel),
            "/api/public/v2/contentnode/{}/".format(node.id),
            "/api/public/v2/contentnode/?channel_id={}".format(channel),
            "/api/public/v2/contentnode_tree/{}/".format(root.id),
            "/api/public/v2/channel/",
            "/api/public/v2/importmetadata/{}/".format(node.id),
            "/api/public/v1/channels",
            "/api/public/v1/channels/lookup/{}".format(channel),
        ]

    def assertNothingLeaks(self, user, node, root, channel, checksum, title):
        client = self.client_for(user)
        for url in self.content_urls(node, root, channel):
            body = client.get(url).content.decode("utf-8")
            who = user.username if user else "anonymous"
            self.assertNotIn(
                node.id, body, "{} got {} via {}".format(who, node.title, url)
            )
            self.assertNotIn(
                checksum, body, "{} got a file checksum via {}".format(who, url)
            )
            self.assertNotIn(
                title, body, "{} got the channel name via {}".format(who, url)
            )

    # ------------------------------------------------------------- learners

    def test_learner_gets_no_other_band_content(self):
        self.assertNothingLeaks(
            self.learner,
            self.g67_video,
            self.g67_root,
            self.g67_channel,
            self.g67_checksum,
            "LSHE G6-7",
        )

    def test_learner_never_sees_teacher_channel(self):
        self.assertNothingLeaks(
            self.learner,
            self.t_video,
            self.t_root,
            TEACHER_CHANNEL,
            self.t_checksum,
            "Teacher CSE course",
        )

    def test_learner_still_gets_assigned_content(self):
        client = self.client_for(self.learner)
        self.assertEqual(
            client.get(
                "/api/content/contentnode/{}/".format(self.g45_video.id)
            ).status_code,
            200,
        )
        channels = client.get("/api/content/channel/").json()
        self.assertEqual([c["id"] for c in channels], [self.g45_channel])
        files = client.get("/api/content/file/").content.decode("utf-8")
        self.assertIn(self.g45_checksum, files)

    def test_teacher_channel_in_band_still_hidden(self):
        # Even if a band row for the teacher channel is added by hand.
        GradeBandChannel.objects.create(band="G4-5", channel_id=TEACHER_CHANNEL)
        self.assertNothingLeaks(
            self.learner,
            self.t_video,
            self.t_root,
            TEACHER_CHANNEL,
            self.t_checksum,
            "Teacher CSE course",
        )

    # ------------------------------------------------------------ signed out

    def test_signed_out_gets_no_content(self):
        for node, root, channel, checksum, title in (
            (
                self.g45_video,
                self.g45_root,
                self.g45_channel,
                self.g45_checksum,
                "LSHE G4-5",
            ),
            (
                self.g67_video,
                self.g67_root,
                self.g67_channel,
                self.g67_checksum,
                "LSHE G6-7",
            ),
            (
                self.t_video,
                self.t_root,
                TEACHER_CHANNEL,
                self.t_checksum,
                "Teacher CSE course",
            ),
        ):
            self.assertNothingLeaks(None, node, root, channel, checksum, title)

    def test_public_content_api_off_for_everyone(self):
        for user in (None, self.learner, self.teacher, self.admin):
            client = self.client_for(user)
            for url in (
                "/api/public/v2/channel/",
                "/api/public/v2/contentnode/{}/".format(self.g45_video.id),
                "/api/public/v2/importmetadata/{}/".format(self.g45_video.id),
                "/api/public/v1/channels",
            ):
                self.assertEqual(client.get(url).status_code, 404, url)

    # ---------------------------------------------------- teachers and admins

    def test_teacher_and_admin_see_teacher_channel(self):
        for user in (self.teacher, self.admin):
            client = self.client_for(user)
            response = client.get(
                "/api/content/contentnode/{}/".format(self.t_video.id)
            )
            self.assertEqual(response.status_code, 200, user.username)
            channel_ids = {c["id"] for c in client.get("/api/content/channel/").json()}
            self.assertIn(TEACHER_CHANNEL, channel_ids)

    def test_teacher_sees_only_own_class(self):
        client = self.client_for(self.teacher)
        classes = {c["name"] for c in client.get("/api/auth/classroom/").json()}
        self.assertEqual(classes, {"Grade 4 A"})
        self.assertFalse(
            self.teacher.has_role_for_collection(role_kinds.ADMIN, self.facility)
        )
        self.assertFalse(
            self.teacher.has_role_for_collection(role_kinds.COACH, self.upper)
        )


class ContentLockdownOffTestCase(BandFixture, TestCase):
    """Without the LSHE lockdown, upstream behaviour is unchanged."""

    @classmethod
    def setUpTestData(cls):
        cls.build()

    @override_settings(LSHE_GRADE_BANDS="off")
    def test_public_api_and_guest_browsing_open(self):
        client = APIClient()
        self.assertEqual(client.get("/api/public/v2/channel/").status_code, 200)
        response = client.get("/api/content/contentnode/{}/".format(self.g67_video.id))
        self.assertEqual(response.status_code, 200)
