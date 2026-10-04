from datetime import timedelta

import pytest

from network_monitor_tds.domain.presence.errors import InvalidWindowError
from network_monitor_tds.domain.presence.models import PresenceInterval
from network_monitor_tds.domain.presence.timeline import hourly_presence, uptime_ratio
from tests.conftest import T0

H = timedelta(hours=1)
M = timedelta(minutes=1)


def interval(start: timedelta, end: timedelta | None) -> PresenceInterval:
    return PresenceInterval(start=T0 + start, end=None if end is None else T0 + end)


@pytest.mark.parametrize(
    ("intervals", "expected"),
    [
        ([], (False, False, False, False)),
        ([interval(H + 10 * M, H + 20 * M)], (False, True, False, False)),
        ([interval(30 * M, 2 * H + 30 * M)], (True, True, True, False)),
        ([interval(H, 2 * H)], (False, True, False, False)),
        ([interval(2 * H + 5 * M, 2 * H + 5 * M)], (False, False, True, False)),
        ([interval(2 * H, 2 * H)], (False, False, True, False)),
        ([interval(3 * H + 30 * M, None)], (False, False, False, True)),
        ([interval(-H, 10 * M), interval(3 * H, 3 * H + M)], (True, False, False, True)),
    ],
)
def test_hourly_presence(intervals: list[PresenceInterval], expected: tuple[bool, ...]) -> None:
    assert hourly_presence(intervals, T0, 4, T0 + 4 * H) == expected


def test_hourly_open_interval_stops_at_now() -> None:
    assert hourly_presence([interval(0 * H, None)], T0, 4, T0 + H + 30 * M) == (
        True,
        True,
        False,
        False,
    )


@pytest.mark.parametrize(
    ("intervals", "expected"),
    [
        ([], 0.0),
        ([interval(0 * H, 4 * H)], 1.0),
        ([interval(H, 2 * H)], 0.25),
        ([interval(-2 * H, H), interval(3 * H, None)], 0.5),
        ([interval(5 * H, 6 * H)], 0.0),
    ],
)
def test_uptime_ratio(intervals: list[PresenceInterval], expected: float) -> None:
    assert uptime_ratio(intervals, T0, T0 + 4 * H, T0 + 4 * H) == pytest.approx(expected)


@pytest.mark.parametrize("length", [timedelta(), -H])
def test_uptime_ratio_rejects_empty_window(length: timedelta) -> None:
    with pytest.raises(InvalidWindowError):
        uptime_ratio([], T0, T0 + length, T0)
