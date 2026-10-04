from datetime import datetime
from typing import Protocol

from network_monitor_tds.domain.errors import NaiveDatetimeError


class Clock(Protocol):
    def now(self) -> datetime: ...


def ensure_aware(value: datetime) -> datetime:
    if value.utcoffset() is None:
        raise NaiveDatetimeError(value)
    return value
