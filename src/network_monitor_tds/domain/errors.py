from datetime import datetime

from network_monitor_tds.errors import NetworkMonitorError


class DomainError(NetworkMonitorError):
    pass


class NaiveDatetimeError(DomainError, ValueError):
    def __init__(self, value: datetime) -> None:
        super().__init__(f"Expected a timezone-aware datetime, got {value.isoformat()}")
