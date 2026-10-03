from datetime import datetime, timedelta

import pytest

from network_monitor_tds.domain.errors import NaiveDatetimeError
from network_monitor_tds.domain.presence.errors import InvalidIntervalError
from network_monitor_tds.domain.presence.models import Presence, PresenceInterval, PresenceState
from tests.conftest import NAIVE, T0


def test_interval_rejects_end_before_start() -> None:
    with pytest.raises(InvalidIntervalError):
        PresenceInterval(start=T0, end=T0 - timedelta(seconds=1))


@pytest.mark.parametrize(("start", "end"), [(NAIVE, None), (T0, NAIVE)])
def test_interval_requires_aware_timestamps(start: datetime, end: datetime | None) -> None:
    with pytest.raises(NaiveDatetimeError):
        PresenceInterval(start=start, end=end)


@pytest.mark.parametrize(
    ("end", "expected"),
    [(T0 + timedelta(hours=1), T0 + timedelta(hours=1)), (None, T0 + timedelta(hours=5))],
)
def test_interval_end_or_now(end: datetime | None, expected: datetime) -> None:
    interval = PresenceInterval(start=T0, end=end)

    assert interval.end_or(T0 + timedelta(hours=5)) == expected


def test_presence_requires_aware_timestamps() -> None:
    with pytest.raises(NaiveDatetimeError):
        Presence(state=PresenceState.ONLINE, changed_at=NAIVE, last_seen=T0)
