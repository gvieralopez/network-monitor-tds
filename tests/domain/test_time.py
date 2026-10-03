import pytest

from network_monitor_tds.domain.errors import NaiveDatetimeError
from network_monitor_tds.domain.time import ensure_aware
from tests.conftest import NAIVE, T0


def test_ensure_aware_returns_aware_datetime() -> None:
    assert ensure_aware(T0) is T0


def test_ensure_aware_rejects_naive_datetime() -> None:
    with pytest.raises(NaiveDatetimeError, match="timezone-aware"):
        ensure_aware(NAIVE)
