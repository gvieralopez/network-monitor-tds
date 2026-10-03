from datetime import datetime

from network_monitor_tds.domain.errors import DomainError


class InvalidLabelError(DomainError, ValueError):
    def __init__(self, field: str) -> None:
        super().__init__(f"Label {field!r} must not be blank")


class InvalidDeviceTimelineError(DomainError, ValueError):
    def __init__(self, first_seen: datetime, last_seen: datetime) -> None:
        super().__init__(
            f"last_seen ({last_seen.isoformat()}) is before first_seen ({first_seen.isoformat()})"
        )
