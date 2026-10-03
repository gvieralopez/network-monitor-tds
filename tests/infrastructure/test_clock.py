from datetime import UTC, datetime

from network_monitor_tds.infrastructure.clock import SystemClock


def test_system_clock_returns_current_utc_time() -> None:
    before = datetime.now(UTC)

    now = SystemClock().now()

    assert now.tzinfo is UTC
    assert before <= now <= datetime.now(UTC)
