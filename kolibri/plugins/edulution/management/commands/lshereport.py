"""
Monthly LSHE (Life Skills and Health Education) report for one centre.

    kolibri manage lshereport --month 2027-03 [--output-dir /srv/lshe-reports]

Writes two files, overwriting any earlier run for the same month:

    lshe_<CENTRE_CODE>_<YYYY-MM>.csv   aggregate figures, no personal data
    lshe_<CENTRE_CODE>_<YYYY-MM>.json  metadata (generation time, version,
                                       facility ids, timezone, definitions)

CENTRE_CODE comes from $KOLIBRI_CENTRE_CODE; the command fails if it is unset.

Who counts: learners only, i.e. users with no role (not coach, admin or
classroom coach) who are not device superusers. Activity in the teacher
channels ($LSHE_TEACHER_CHANNEL_IDS, or the LSHE_TEACHER_CHANNEL_IDS Django
setting) is left out of every figure.

Metrics, per class and gender, plus a centre total:

    enrolled_learners    learners in the class at the end of the month
    active_learners      learners with at least one session (UserSessionLog)
                         starting in the month
    sessions             sessions (UserSessionLog) starting in the month
    reached_new          learners whose first fully completed item
                         (ContentSummaryLog progress = 1) falls in the month
    reached_cumulative   learners with a fully completed item by the end of
                         the month (UNESCO "reached")
    completions          items reaching progress = 1 in the month, by
                         completion_timestamp
    video_watch_seconds  time_spent in video sessions (ContentSessionLog)
                         ending in the month

Month boundaries are midnight on the 1st in $LSHE_REPORT_TIMEZONE (default
Africa/Lusaka), independent of the container's own timezone.

Class history: Kolibri keeps no history of class memberships, so the first
time a finished month is reported, each learner's class and gender is saved
(LSHEMonthlyEnrolment) and every re-run of that month uses that snapshot.
A month that has not finished yet is reported from current classes and is
not saved.
"""
import csv
import datetime
import io
import json
import os
import re
from collections import defaultdict

import pytz
from django.core.management.base import BaseCommand
from django.core.management.base import CommandError
from django.db import transaction
from django.db.models import Count
from django.db.models import Min
from django.db.models import Q
from django.db.models import Sum

import kolibri
from kolibri.core.auth.constants.demographics import FEMALE
from kolibri.core.auth.constants.demographics import MALE
from kolibri.core.auth.constants.demographics import NOT_SPECIFIED
from kolibri.core.auth.models import Facility
from kolibri.core.auth.models import FacilityUser
from kolibri.core.auth.models import Membership
from kolibri.core.logger.models import ContentSessionLog
from kolibri.core.logger.models import ContentSummaryLog
from kolibri.core.logger.models import UserSessionLog
from kolibri.plugins.edulution.lshe_settings import teacher_channel_ids
from kolibri.plugins.edulution.models import LSHEMonthlyEnrolment

REPORT_VERSION = 1
DEFAULT_TIMEZONE = "Africa/Lusaka"
DEFAULT_OUTPUT_DIR = "/srv/lshe-reports"

GENDERS = (MALE, FEMALE, NOT_SPECIFIED)
ALL = "ALL"
CENTRE_TOTAL = "CENTRE_TOTAL"
NO_CLASS = "NO_CLASS"

METRICS = (
    "enrolled_learners",
    "active_learners",
    "sessions",
    "reached_new",
    "reached_cumulative",
    "completions",
    "video_watch_seconds",
)
COLUMNS = ("centre_code", "month", "class", "gender") + METRICS

CENTRE_CODE_RE = re.compile(r"^[A-Za-z0-9_-]{1,32}$")
MONTH_RE = re.compile(r"^(\d{4})-(\d{2})$")


def parse_month(value):
    match = MONTH_RE.match(value or "")
    if not match or not 1 <= int(match.group(2)) <= 12:
        raise CommandError("--month must be YYYY-MM, e.g. 2027-03")
    return int(match.group(1)), int(match.group(2))


def month_bounds(year, month, tz):
    """[start, end) of the month as timezone-aware datetimes in `tz`."""
    start = tz.localize(datetime.datetime(year, month, 1))
    if month == 12:
        end = tz.localize(datetime.datetime(year + 1, 1, 1))
    else:
        end = tz.localize(datetime.datetime(year, month + 1, 1))
    return start, end


def normalise_gender(value):
    return value if value in (MALE, FEMALE) else NOT_SPECIFIED


def learner_users():
    """Users with no role who are not device superusers (soft-deleted included)."""
    return FacilityUser.objects.filter(roles__isnull=True).exclude(
        devicepermissions__is_superuser=True
    )


def current_enrolment(end):
    """[(user_id, class_name, gender, deleted)] from today's class memberships."""
    learners = learner_users().filter(date_joined__lt=end)
    users = {u["id"]: u for u in learners.values("id", "gender", "deleted")}
    classes = defaultdict(set)
    for user_id, class_name in Membership.objects.filter(
        user_id__in=list(users), collection__kind="classroom"
    ).values_list("user_id", "collection__name"):
        classes[user_id].add(class_name)
    rows = []
    for user_id, u in users.items():
        for class_name in sorted(classes.get(user_id) or [""]):
            rows.append(
                (user_id, class_name, normalise_gender(u["gender"]), u["deleted"])
            )
    return rows


class Command(BaseCommand):
    help = "Write the monthly LSHE report (aggregate figures only) for this centre."

    def add_arguments(self, parser):
        parser.add_argument("--month", required=True, help="Month to report, YYYY-MM")
        parser.add_argument(
            "--output-dir",
            default=os.environ.get("LSHE_REPORT_DIR", DEFAULT_OUTPUT_DIR),
            help="Directory for the report files (default: $LSHE_REPORT_DIR or {})".format(
                DEFAULT_OUTPUT_DIR
            ),
        )

    # -------------------------------------------------------------- enrolment

    def enrolment(self, month, end, now):
        """
        Return (rows, snapshot_taken_at or None) for the month. A finished
        month is saved on first use and read back afterwards.
        """
        saved = LSHEMonthlyEnrolment.objects.filter(month=month)
        if saved.exists():
            rows = list(saved.values_list("user_id", "class_name", "gender", "deleted"))
            return rows, saved.aggregate(t=Min("taken_at"))["t"]
        rows = current_enrolment(end)
        if now < end:
            return rows, None  # month not finished: do not freeze it yet
        with transaction.atomic():
            LSHEMonthlyEnrolment.objects.bulk_create(
                LSHEMonthlyEnrolment(
                    month=month,
                    user_id=user_id,
                    class_name=class_name,
                    gender=gender,
                    deleted=deleted,
                    taken_at=now,
                )
                for user_id, class_name, gender, deleted in rows
            )
        return rows, now

    # ---------------------------------------------------------------- metrics

    def per_learner(self, user_ids, start, end, excluded_channels):
        """{metric: {user_id: value}} for the month."""
        not_teacher = ~Q(channel_id__in=excluded_channels) if excluded_channels else Q()
        # Completed items, read once and folded in Python: timestamps are
        # stored as text, so comparing parsed datetimes here is exact. Older
        # logs may lack completion_timestamp; fall back to end_timestamp.
        first_done = {}
        completions = defaultdict(int)
        for user_id, completed_at, ended_at in ContentSummaryLog.objects.filter(
            not_teacher, user_id__in=user_ids, progress__gte=1
        ).values_list("user_id", "completion_timestamp", "end_timestamp"):
            done_at = completed_at or ended_at
            if done_at is None:
                continue
            if user_id not in first_done or done_at < first_done[user_id]:
                first_done[user_id] = done_at
            if start <= done_at < end:
                completions[user_id] += 1
        video = dict(
            ContentSessionLog.objects.filter(
                not_teacher,
                user_id__in=user_ids,
                kind="video",
                end_timestamp__gte=start,
                end_timestamp__lt=end,
            )
            .values("user_id")
            .annotate(s=Sum("time_spent"))
            .values_list("user_id", "s")
        )
        sessions = dict(
            UserSessionLog.objects.filter(
                user_id__in=user_ids,
                start_timestamp__gte=start,
                start_timestamp__lt=end,
            )
            .values("user_id")
            .annotate(n=Count("id"))
            .values_list("user_id", "n")
        )
        return {
            "reached_new": {
                u for u, t in first_done.items() if t is not None and start <= t < end
            },
            "reached_cumulative": {
                u for u, t in first_done.items() if t is not None and t < end
            },
            "completions": completions,
            "video": video,
            "sessions": sessions,
        }

    @staticmethod
    def aggregate(members, data):
        """Figures for a group. `members` is {user_id: deleted}."""
        ids = set(members)
        return {
            "enrolled_learners": sum(1 for d in members.values() if not d),
            "active_learners": len(ids & set(data["sessions"])),
            "sessions": sum(data["sessions"].get(u, 0) for u in ids),
            "reached_new": len(ids & data["reached_new"]),
            "reached_cumulative": len(ids & data["reached_cumulative"]),
            "completions": sum(data["completions"].get(u, 0) for u in ids),
            "video_watch_seconds": int(
                round(sum(data["video"].get(u) or 0 for u in ids))
            ),
        }

    def build_rows(self, centre_code, month, enrolment, data):
        # group -> {user_id: deleted}; a learner in two classes counts in both
        # classes but only once in the centre total.
        groups = defaultdict(dict)
        for user_id, class_name, gender, deleted in enrolment:
            label = class_name or NO_CLASS
            for key in (
                (label, gender),
                (label, ALL),
                (CENTRE_TOTAL, gender),
                (CENTRE_TOTAL, ALL),
            ):
                groups[key][user_id] = deleted and groups[key].get(user_id, True)

        class_labels = sorted({c for c, _ in groups if c != CENTRE_TOTAL})
        rows = []
        for label in class_labels + [CENTRE_TOTAL]:
            for gender in GENDERS + (ALL,):
                figures = self.aggregate(groups.get((label, gender), {}), data)
                row = {
                    "centre_code": centre_code,
                    "month": month,
                    "class": label,
                    "gender": gender,
                }
                row.update(figures)
                rows.append(row)
        return rows

    # ----------------------------------------------------------------- output

    @staticmethod
    def write_atomic(path, text):
        tmp = path + ".tmp"
        with io.open(tmp, "w", encoding="utf-8", newline="") as f:
            f.write(text)
        os.replace(tmp, path)

    def handle(self, *args, **options):
        centre_code = os.environ.get("KOLIBRI_CENTRE_CODE", "").strip()
        if not centre_code:
            raise CommandError("Set KOLIBRI_CENTRE_CODE (e.g. in the deployment .env)")
        if not CENTRE_CODE_RE.match(centre_code):
            raise CommandError(
                "KOLIBRI_CENTRE_CODE may only contain letters, digits, '_' and '-' (max 32)"
            )
        tz_name = os.environ.get("LSHE_REPORT_TIMEZONE", DEFAULT_TIMEZONE)
        try:
            tz = pytz.timezone(tz_name)
        except pytz.UnknownTimeZoneError:
            raise CommandError("Unknown LSHE_REPORT_TIMEZONE: {}".format(tz_name))

        year, mon = parse_month(options["month"])
        month = "{:04d}-{:02d}".format(year, mon)
        start, end = month_bounds(year, mon, tz)
        now = datetime.datetime.now(pytz.utc)
        if now < start:
            raise CommandError("{} has not started yet".format(month))

        output_dir = options["output_dir"]
        if not os.path.isdir(output_dir):
            raise CommandError("Output directory does not exist: {}".format(output_dir))

        try:
            excluded = teacher_channel_ids()
        except ValueError as e:
            raise CommandError(str(e))
        enrolment, snapshot_at = self.enrolment(month, end, now)
        data = self.per_learner(
            list({row[0] for row in enrolment}), start, end, excluded
        )
        rows = self.build_rows(centre_code, month, enrolment, data)

        out = io.StringIO()
        writer = csv.DictWriter(out, fieldnames=COLUMNS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)

        base = os.path.join(output_dir, "lshe_{}_{}".format(centre_code, month))
        self.write_atomic(base + ".csv", out.getvalue())
        metadata = {
            "report": "lshe_monthly",
            "report_version": REPORT_VERSION,
            "centre_code": centre_code,
            "month": month,
            "timezone": tz_name,
            "month_start": start.isoformat(),
            "month_end_exclusive": end.isoformat(),
            "month_complete": now >= end,
            "class_snapshot_taken_at": snapshot_at.isoformat() if snapshot_at else None,
            "generated_at": now.isoformat(),
            "kolibri_version": kolibri.__version__,
            "facility_ids": sorted(Facility.objects.values_list("id", flat=True)),
            "excluded_teacher_channel_ids": excluded,
            "columns": list(COLUMNS),
            "definitions": {
                "learners": "users with no role who are not device superusers",
                "enrolled_learners": "learners in the class at the end of the month",
                "active_learners": "learners with a UserSessionLog starting in the month",
                "sessions": "UserSessionLog rows starting in the month",
                "reached_new": "learners whose first ContentSummaryLog with progress = 1 is in the month",
                "reached_cumulative": "learners with a ContentSummaryLog with progress = 1 before the end of the month",
                "completions": "ContentSummaryLog rows reaching progress = 1 in the month (completion_timestamp)",
                "video_watch_seconds": "sum of ContentSessionLog.time_spent for kind = video, by end_timestamp in the month",
            },
        }
        self.write_atomic(
            base + ".json", json.dumps(metadata, indent=2, sort_keys=True) + "\n"
        )
        if now < end:
            self.stdout.write(
                self.style.WARNING(
                    "{} has not finished: figures are partial and classes were not saved.".format(
                        month
                    )
                )
            )
        self.stdout.write("Wrote {}.csv and {}.json".format(base, base))
