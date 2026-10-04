from datetime import timedelta

import pytest

from network_monitor_tds.domain.retention.errors import InvalidRetentionError
from network_monitor_tds.domain.retention.models import RetentionPolicy
from tests.conftest import T0


@pytest.mark.parametrize("keep_days", [14, 90, 3650])
def test_retention_accepts_days_in_range(keep_days: int) -> None:
    assert RetentionPolicy(keep_days).cutoff(T0) == T0 - timedelta(days=keep_days)


@pytest.mark.parametrize("keep_days", [-1, 0, 13, 3651])
def test_retention_rejects_days_out_of_range(keep_days: int) -> None:
    with pytest.raises(InvalidRetentionError, match="14 to 3650 days"):
        RetentionPolicy(keep_days)
