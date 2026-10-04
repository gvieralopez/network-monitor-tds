from datetime import datetime
from ipaddress import IPv4Address
from typing import Self

from pydantic import BaseModel, ConfigDict

from network_monitor_tds.application.models import DeviceSummary
from network_monitor_tds.domain.devices.models import Category


class DeviceOut(BaseModel):
    model_config = ConfigDict(frozen=True)

    mac: str
    ip: IPv4Address | None
    name: str
    category: Category
    vendor: str | None
    online: bool
    new: bool
    first_seen: datetime
    last_seen: datetime

    @classmethod
    def from_summary(cls, summary: DeviceSummary) -> Self:
        device = summary.device
        return cls(
            mac=device.mac.value,
            ip=device.ip,
            name=summary.name.value,
            category=summary.category.value,
            vendor=summary.vendor,
            online=summary.online,
            new=summary.is_new,
            first_seen=device.first_seen,
            last_seen=device.last_seen,
        )
