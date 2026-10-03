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
    ("offline_after", "mobile_offline_after"),
    [(timedelta(), timedelta(minutes=5)), (timedelta(minutes=5), timedelta(seconds=-1))],
)
def test_policy_rejects_non_positive_thresholds(
    offline_after: timedelta, mobile_offline_after: timedelta
) -> None:
    with pytest.raises(InvalidPolicyError, match="positive"):
        PresencePolicy(offline_after=offline_after, mobile_offline_after=mobile_offline_after)
