"""
Time logged in (the coach's attendance report) must include time spent
watching: a learner watching a video touches nothing, so the browser
heartbeat reports them idle, and only the progress the video reports shows
they are there. All data here is invented.
"""
import uuid
from datetime import timedelta

from django.test import override_settings
from django.urls import reverse
from rest_framework.test import APITestCase

from kolibri.core.logger.models import UserSessionLog
from kolibri.plugins.edulution.test.test_grade_bands import BandFixture
from kolibri.plugins.edulution.test.test_grade_bands import PASSWORD
from kolibri.utils.time_utils import local_now


@override_settings(LSHE_GRADE_BANDS="off")
class WatchingCountsAsLoggedInTestCase(BandFixture, APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.build()
        cls.learner.set_password(PASSWORD)
        cls.learner.save()

    def setUp(self):
        self.client.login(
            username=self.learner.username, password=PASSWORD, facility=self.facility
        )

    def session(self, minutes_ago):
        when = local_now() - timedelta(minutes=minutes_ago)
        log = UserSessionLog.objects.create(
            user=self.learner, device_info="Android,12/Chrome,120"
        )
        UserSessionLog.objects.filter(pk=log.pk).update(
            start_timestamp=when, last_interaction_timestamp=when
        )
        return log

    def watch(self):
        start = self.client.post(
            reverse("kolibri:core:trackprogress-list"),
            {
                "node_id": self.g45_video.id,
                "content_id": uuid.uuid4().hex,
                "channel_id": self.g45_channel,
                "kind": "video",
            },
            format="json",
        )
        self.assertEqual(start.status_code, 200)
        update = self.client.put(
            reverse(
                "kolibri:core:trackprogress-detail",
                kwargs={"pk": start.data["session_id"]},
            ),
            {"progress_delta": 0.2, "time_spent_delta": 30},
            format="json",
        )
        self.assertEqual(update.status_code, 200)

    def test_watching_extends_the_session(self):
        log = self.session(minutes_ago=3)
        self.watch()
        log.refresh_from_db()
        logged_in = log.last_interaction_timestamp - log.start_timestamp
        self.assertGreater(logged_in, timedelta(minutes=2))
        self.assertEqual(UserSessionLog.objects.filter(user=self.learner).count(), 1)

    def test_after_a_long_gap_a_new_session_on_the_same_device(self):
        self.session(minutes_ago=30)
        self.watch()
        logs = UserSessionLog.objects.filter(user=self.learner).order_by(
            "start_timestamp"
        )
        self.assertEqual(logs.count(), 2)
        self.assertEqual(logs[1].device_info, "Android,12/Chrome,120")
