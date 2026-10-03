from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum

from network_monitor_tds.domain.network.models import MacAddress
from network_monitor_tds.domain.time import ensure_aware


class EventKind(StrEnum):
    DEVICE_DISCOVERED = "device_discovered"
    DEVICE_ONLINE = "device_online"
    DEVICE_OFFLINE = "device_offline"


@dataclass(frozen=True, slots=True)
class DeviceEvent:
    kind: EventKind
    mac: MacAddress
    occurred_at: datetime

    def __post_init__(self) -> None:
        ensure_aware(self.occurred_at)
