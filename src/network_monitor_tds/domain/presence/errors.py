from datetime import datetime, timedelta

from network_monitor_tds.domain.errors import DomainError


class InvalidIntervalError(DomainError, ValueError):
    def __init__(self, start: datetime, end: datetime) -> None:
        super().__init__(
            f"Interval ends ({end.isoformat()}) before it starts ({start.isoformat()})"
        )


class InvalidPolicyError(DomainError, ValueError):
    def __init__(self, reason: str) -> None:
        super().__init__(f"Invalid presence policy: {reason}")


class InvalidWindowError(DomainError, ValueError):
    def __init__(self, length: timedelta) -> None:
        super().__init__(f"Time window must have a positive length, got {length}")
