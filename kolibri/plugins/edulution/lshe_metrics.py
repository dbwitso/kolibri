"""
The LSHE (Life Skills and Health Education) figures, in one place.

The monthly report for UNESCO (lshe_report.py in kolibri_helper_scripts) and
the coach's Monthly reports page both use these, so a class's figures are
the same on screen and in the file sent on.

Who counts: learners, i.e. users with no role who are not device superusers.
Activity in the teacher channels (LSHE_TEACHER_CHANNEL_IDS) is left out.

    enrolled_learners    learners in the class (not soft-deleted)
    active_learners      learners with a session (UserSessionLog) starting in
                         the period
    sessions             sessions starting in the period
    reached_new          learners whose first fully completed item
                         (ContentSummaryLog progress = 1) is in the period
    reached_cumulative   learners with a fully completed item by the end of
                         the period (UNESCO "reached")
    completions          items reaching progress = 1 in the period
    video_watch_seconds  time spent in video sessions (ContentSessionLog)
                         ending in the period
    logged_in_seconds    time signed in during sessions starting in the
                         period (last interaction minus start), as the
                         attendance report counts it

Periods run from midnight in LSHE_REPORT_TIMEZONE (default Africa/Lusaka),
whatever the server's own time zone.
"""
import datetime
import os
from collections import defaultdict

import pytz
from django.conf import settings
from django.db.models import Count
from django.db.models import Q
from django.db.models import Sum

from kolibri.core.auth.constants.demographics import FEMALE
from kolibri.core.auth.constants.demographics import MALE
from kolibri.core.auth.constants.demographics import NOT_SPECIFIED
from kolibri.core.auth.models import FacilityUser
from kolibri.core.auth.models import Membership
from kolibri.core.logger.models import ContentSessionLog
from kolibri.core.logger.models import ContentSummaryLog
from kolibri.core.logger.models import UserSessionLog
from kolibri.plugins.edulution.lshe_settings import teacher_channel_ids

DEFAULT_TIMEZONE = "Africa/Lusaka"
GENDERS = (MALE, FEMALE, NOT_SPECIFIED)
ALL = "ALL"
DAY = "day"
WEEK = "week"
MONTH = "month"
PERIODS = (DAY, WEEK, MONTH)
TREND_MONTHS = 6


def report_timezone():
    name = os.environ.get("LSHE_REPORT_TIMEZONE") or getattr(
        settings, "LSHE_REPORT_TIMEZONE", DEFAULT_TIMEZONE
    )
    try:
        return pytz.timezone(name)
    except pytz.UnknownTimeZoneError:
        return pytz.timezone(DEFAULT_TIMEZONE)


def excluded_channels():
    """The teacher channels, whose activity no figure counts."""
    try:
        return teacher_channel_ids()
    except ValueError:
        return []


def normalise_gender(value):
    return value if value in (MALE, FEMALE) else NOT_SPECIFIED


def learner_users():
    """Users with no role who are not device superusers (soft-deleted included)."""
    return FacilityUser.objects.filter(roles__isnull=True).exclude(
        devicepermissions__is_superuser=True
    )


# ---------------------------------------------------------------- figures


def per_learner(user_ids, start, end, excluded_channels):
    """{metric: {user_id: value}} for [start, end)."""
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
        "video_watch_seconds": int(round(sum(data["video"].get(u) or 0 for u in ids))),
    }


# ---------------------------------------------------------------- periods


def _midnight(tz, day):
    return tz.localize(datetime.datetime(day.year, day.month, day.day))


def _month_start(day):
    return datetime.date(day.year, day.month, 1)


def _add_months(day, months):
    index = day.year * 12 + day.month - 1 + months
    return datetime.date(index // 12, index % 12 + 1, 1)


def period_bounds(period, day, tz):
    """
    (start, end, buckets) for the period containing `day`: [start, end) in
    `tz`, and the chart's buckets as (start, end, key) - hours of a day, or
    days of a week (Monday to Sunday) or month.
    """
    if period == DAY:
        start = _midnight(tz, day)
        end = _midnight(tz, day + datetime.timedelta(days=1))
        buckets = []
        for hour in range(24):
            b_start = tz.normalize(start + datetime.timedelta(hours=hour))
            buckets.append(
                (b_start, tz.normalize(b_start + datetime.timedelta(hours=1)), hour)
            )
        return start, end, buckets
    if period == WEEK:
        first = day - datetime.timedelta(days=day.weekday())
        days = [first + datetime.timedelta(days=i) for i in range(7)]
    else:
        first = _month_start(day)
        last = _add_months(first, 1)
        days = [first + datetime.timedelta(days=i) for i in range((last - first).days)]
    buckets = [
        (
            _midnight(tz, d),
            _midnight(tz, d + datetime.timedelta(days=1)),
            d.isoformat(),
        )
        for d in days
    ]
    return buckets[0][0], buckets[-1][1], buckets


# ---------------------------------------------------------------- the class


def class_members(classroom, month=None):
    """
    ({user_id: (gender, deleted)}, from_record) for the class's learners. For
    a finished month the monthly report already saved (LSHEMonthlyEnrolment),
    its record is used (from_record True), so the page shows the same
    learners as the file sent on.
    """
    if month:
        from kolibri.plugins.edulution.models import LSHEMonthlyEnrolment

        saved = LSHEMonthlyEnrolment.objects.filter(
            month=month, class_name=classroom.name
        ).values_list("user_id", "gender", "deleted")
        if saved:
            return {u: (normalise_gender(g), d) for u, g, d in saved}, True
    learner_ids = Membership.objects.filter(collection=classroom).values_list(
        "user_id", flat=True
    )
    members = {
        u["id"]: (normalise_gender(u["gender"]), u["deleted"])
        for u in learner_users()
        .filter(id__in=learner_ids)
        .values("id", "gender", "deleted")
    }
    return members, False


def _totals(members, data):
    """{gender or ALL: figures}."""
    out = {}
    for gender in GENDERS + (ALL,):
        group = {
            u: deleted
            for u, (g, deleted) in members.items()
            if gender == ALL or g == gender
        }
        out[gender] = aggregate(group, data)
    return out


def _sessions(user_ids, start, end):
    return list(
        UserSessionLog.objects.filter(
            user_id__in=user_ids,
            start_timestamp__gte=start,
            start_timestamp__lt=end,
        ).values_list("user_id", "start_timestamp", "last_interaction_timestamp")
    )


def _logged_in(sessions):
    seconds = defaultdict(float)
    last_seen = {}
    for user_id, started, last in sessions:
        if last and last > started:
            seconds[user_id] += (last - started).total_seconds()
        seen = last or started
        if user_id not in last_seen or seen > last_seen[user_id]:
            last_seen[user_id] = seen
    return seconds, last_seen


def _bucket_index(buckets, when):
    """The index of the bucket holding `when`, or None."""
    if when is None:
        return None
    for i, (b_start, b_end, _) in enumerate(buckets):
        if b_start <= when < b_end:
            return i
    return None


def _completion_times(user_ids, start, end, not_teacher):
    for completed_at, ended_at in ContentSummaryLog.objects.filter(
        not_teacher, user_id__in=user_ids, progress__gte=1
    ).values_list("completion_timestamp", "end_timestamp"):
        done_at = completed_at or ended_at
        if done_at is not None and start <= done_at < end:
            yield done_at


def _bucket_series(buckets, user_ids, sessions, start, end, excluded):
    """Per bucket: active learners, sessions, completions, video seconds."""
    not_teacher = ~Q(channel_id__in=excluded) if excluded else Q()
    active = [set() for _ in buckets]
    session_counts = [0] * len(buckets)
    completions = [0] * len(buckets)
    video = [0.0] * len(buckets)
    for user_id, started, _ in sessions:
        i = _bucket_index(buckets, started)
        if i is not None:
            active[i].add(user_id)
            session_counts[i] += 1
    for done_at in _completion_times(user_ids, start, end, not_teacher):
        i = _bucket_index(buckets, done_at)
        if i is not None:
            completions[i] += 1
    for ended_at, spent in ContentSessionLog.objects.filter(
        not_teacher,
        user_id__in=user_ids,
        kind="video",
        end_timestamp__gte=start,
        end_timestamp__lt=end,
    ).values_list("end_timestamp", "time_spent"):
        i = _bucket_index(buckets, ended_at)
        if i is not None:
            video[i] += spent or 0
    return [
        {
            "key": key,
            "active_learners": len(active[i]),
            "sessions": session_counts[i],
            "completions": completions[i],
            "video_watch_seconds": int(round(video[i])),
        }
        for i, (_, _, key) in enumerate(buckets)
    ]


def class_report(classroom, period, day, now=None):
    """
    Everything the coach's Monthly reports page shows for a class: the
    period's figures by gender, a chart series, the last six months, and a
    row per learner (names are added by the API, for the class's coaches).
    """
    tz = report_timezone()
    now = now or datetime.datetime.now(pytz.utc)
    start, end, buckets = period_bounds(period, day, tz)
    month = start.strftime("%Y-%m") if period == MONTH and now >= end else None
    members, from_record = class_members(classroom, month)
    user_ids = list(members)
    excluded = excluded_channels()

    data = per_learner(user_ids, start, end, excluded)
    sessions = _sessions(user_ids, start, end)
    logged_in, last_seen = _logged_in(sessions)
    totals = _totals(members, data)
    for gender, figures in totals.items():
        figures["logged_in_seconds"] = int(
            round(
                sum(
                    logged_in.get(u, 0)
                    for u, (g, _) in members.items()
                    if gender == ALL or g == gender
                )
            )
        )

    trend = []
    first_month = _add_months(
        _month_start(start.astimezone(tz).date()), 1 - TREND_MONTHS
    )
    for i in range(TREND_MONTHS):
        m_start_day = _add_months(first_month, i)
        m_start = _midnight(tz, m_start_day)
        m_end = _midnight(tz, _add_months(m_start_day, 1))
        figures = aggregate(
            {u: d for u, (_, d) in members.items()},
            per_learner(user_ids, m_start, m_end, excluded),
        )
        figures["month"] = m_start_day.strftime("%Y-%m")
        trend.append(figures)

    learners = []
    for user_id, (gender, deleted) in members.items():
        if deleted:
            continue
        learners.append(
            {
                "id": user_id,
                "gender": gender,
                "sessions": data["sessions"].get(user_id, 0),
                "logged_in_seconds": int(round(logged_in.get(user_id, 0))),
                "video_watch_seconds": int(round(data["video"].get(user_id) or 0)),
                "completions": data["completions"].get(user_id, 0),
                "reached": user_id in data["reached_cumulative"],
                "reached_new": user_id in data["reached_new"],
                "last_active": last_seen.get(user_id),
            }
        )

    return {
        "period": period,
        "start": start.isoformat(),
        "end": end.isoformat(),
        "timezone": tz.zone,
        "complete": now >= end,
        # The finished month whose saved class record gave the learners.
        "class_record_month": month if from_record else None,
        "totals": totals,
        "series": _bucket_series(buckets, user_ids, sessions, start, end, excluded),
        "trend": trend,
        "learners": learners,
    }
