from collections.abc import Mapping
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from enum import StrEnum

from network_monitor_tds.domain.devices.models import Category, Device, Resolved
from network_monitor_tds.domain.observations.models import Detection, Fact


@dataclass(frozen=True, slots=True)
class Backoff:
    initial: timedelta
    maximum: timedelta


class HourState(StrEnum):
    ONLINE = "online"
    OFFLINE = "offline"
    UNKNOWN = "unknown"


@dataclass(frozen=True, slots=True)
class DeviceSummary:
    device: Device
    name: Resolved[str]
    category: Resolved[Category]
    vendor: str | None
    online: bool
    last_24_hours: tuple[bool, ...]

    @property
    def is_new(self) -> bool:
        return not self.device.acknowledged

    @property
    def hours_online(self) -> int:
        return sum(self.last_24_hours)


@dataclass(frozen=True, slots=True)
class NetworkOverview:
    total: int
    online: int
    new: int
    seen_per_hour: tuple[int, ...]


@dataclass(frozen=True, slots=True)
class DayPresence:
    day: date
    hours: tuple[HourState, ...]


@dataclass(frozen=True, slots=True)
class DeviceDetail:
    summary: DeviceSummary
    facts: Mapping[str, Fact]
    detections: tuple[Detection, ...]
    days: tuple[DayPresence, ...]
    uptime_last_7_days: float


class PluginState(StrEnum):
    STOPPED = "stopped"
    RUNNING = "running"
    FAILING = "failing"


@dataclass(frozen=True, slots=True)
class PluginStatus:
    state: PluginState
    last_success: datetime | None
    last_error: str | None


STOPPED = PluginStatus(state=PluginState.STOPPED, last_success=None, last_error=None)
