from datetime import timedelta

import pytest

from network_monitor_tds.domain.devices.models import Category
from network_monitor_tds.domain.presence.errors import InvalidPolicyError
from network_monitor_tds.domain.presence.policy import DEFAULT_POLICY, PresencePolicy


@pytest.mark.parametrize(
    ("category", "timeout"),
    [
        (Category.SERVER, timedelta(minutes=10)),
        (Category.UNKNOWN, timedelta(minutes=10)),
        (Category.PHONE, timedelta(minutes=15)),
        (Category.TABLET, timedelta(minutes=15)),
    ],
)
def test_default_policy_timeouts(category: Category, timeout: timedelta) -> None:
    assert DEFAULT_POLICY.timeout_for(category) == timeout


@pytest.mark.parametrize(
    ("interval", "missed", "mobile_missed", "reason"),
    [
        (timedelta(), 2, 3, "sweep_interval"),
        (timedelta(minutes=-5), 2, 3, "sweep_interval"),
        (timedelta(minutes=5), 0, 3, "at least 1"),
        (timedelta(minutes=5), 2, 0, "at least 1"),
    ],
)
def test_policy_validation(
    interval: timedelta, missed: int, mobile_missed: int, reason: str
) -> None:
    with pytest.raises(InvalidPolicyError, match=reason):
        PresencePolicy(
            sweep_interval=interval, missed_sweeps=missed, mobile_missed_sweeps=mobile_missed
        )
