from collections.abc import Sequence
from datetime import datetime, timedelta

from network_monitor_tds.domain.presence.errors import InvalidWindowError
from network_monitor_tds.domain.presence.models import PresenceInterval

HOUR = timedelta(hours=1)


def hourly_presence(
    intervals: Sequence[PresenceInterval], start: datetime, hours: int, now: datetime
) -> tuple[bool, ...]:
    return tuple(
        _touches_any(intervals, start + HOUR * slot, start + HOUR * (slot + 1), now)
        for slot in range(hours)
    )


def uptime_ratio(
    intervals: Sequence[PresenceInterval],
    window_start: datetime,
    window_end: datetime,
    now: datetime,
) -> float:
    length = window_end - window_start
    if length <= timedelta():
        raise InvalidWindowError(length)
    online = sum(
        (_overlap(interval, window_start, window_end, now) for interval in intervals), timedelta()
    )
    return online / length


def _touches_any(
    intervals: Sequence[PresenceInterval], start: datetime, end: datetime, now: datetime
) -> bool:
    return any(_touches(interval, start, end, now) for interval in intervals)


def _touches(interval: PresenceInterval, start: datetime, end: datetime, now: datetime) -> bool:
    interval_end = interval.end_or(now)
    if interval_end == interval.start:
        return start <= interval.start < end
    return interval.start < end and interval_end > start


def _overlap(
    interval: PresenceInterval, start: datetime, end: datetime, now: datetime
) -> timedelta:
    return max(timedelta(), min(interval.end_or(now), end) - max(interval.start, start))
