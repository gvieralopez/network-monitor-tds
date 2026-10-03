from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum

from network_monitor_tds.domain.events.models import DeviceEvent
from network_monitor_tds.domain.presence.errors import InvalidIntervalError
from network_monitor_tds.domain.time import ensure_aware


class PresenceState(StrEnum):
    ONLINE = "online"
    OFFLINE = "offline"


@dataclass(frozen=True, slots=True)
class Presence:
    state: PresenceState
    changed_at: datetime
    last_seen: datetime

    def __post_init__(self) -> None:
        ensure_aware(self.changed_at)
        ensure_aware(self.last_seen)


@dataclass(frozen=True, slots=True)
class PresenceUpdate:
    presence: Presence
    event: DeviceEvent | None


@dataclass(frozen=True, slots=True)
class PresenceInterval:
    start: datetime
    end: datetime | None

    def __post_init__(self) -> None:
        ensure_aware(self.start)
        if self.end is not None and ensure_aware(self.end) < self.start:
            raise InvalidIntervalError(self.start, self.end)

    def end_or(self, now: datetime) -> datetime:
        return self.end if self.end is not None else now
