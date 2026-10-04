import re
from dataclasses import dataclass, replace
from datetime import datetime
from enum import StrEnum
from ipaddress import IPv4Address
from typing import Self

from network_monitor_tds.domain.devices.errors import InvalidDeviceTimelineError, InvalidLabelError
from network_monitor_tds.domain.network.models import MacAddress
from network_monitor_tds.domain.observations.models import KnownField
from network_monitor_tds.domain.time import ensure_aware


class Category(StrEnum):
    NETWORK = "network"
    SERVER = "server"
    COMPUTER = "computer"
    PHONE = "phone"
    TABLET = "tablet"
    MEDIA = "media"
    IOT = "iot"
    CAMERA = "camera"
    PRINTER = "printer"
    UNKNOWN = "unknown"

    @property
    def is_mobile(self) -> bool:
        return self in {Category.PHONE, Category.TABLET}


class Fallback(StrEnum):
    USER = "user"
    MAC_ADDRESS = "mac_address"
    DEFAULT = "default"


type Origin = KnownField | Fallback

_NON_ALPHANUMERIC = re.compile(r"[^a-z0-9]+")


@dataclass(frozen=True, slots=True)
class Resolved[T]:
    value: T
    origin: Origin


@dataclass(frozen=True, slots=True)
class ClassificationRule:
    category: Category
    fragments: tuple[str, ...]
    words: tuple[str, ...]

    def matches(self, text: str) -> bool:
        lowered = text.lower()
        compact = _NON_ALPHANUMERIC.sub("", lowered)
        tokens = set(_NON_ALPHANUMERIC.split(lowered))
        has_fragment = any(fragment in compact for fragment in self.fragments)
        has_word = not tokens.isdisjoint(self.words)
        return has_fragment or has_word


@dataclass(frozen=True, slots=True)
class DeviceLabels:
    name: str | None
    category: Category | None
    icon: str | None

    def __post_init__(self) -> None:
        for field, value in (("name", self.name), ("icon", self.icon)):
            if value is not None and not value.strip():
                raise InvalidLabelError(field)


NO_LABELS = DeviceLabels(name=None, category=None, icon=None)


@dataclass(frozen=True, slots=True)
class Device:
    mac: MacAddress
    ip: IPv4Address | None
    first_seen: datetime
    last_seen: datetime
    acknowledged: bool
    labels: DeviceLabels

    def __post_init__(self) -> None:
        ensure_aware(self.first_seen)
        ensure_aware(self.last_seen)
        if self.last_seen < self.first_seen:
            raise InvalidDeviceTimelineError(self.first_seen, self.last_seen)

    @classmethod
    def discovered(cls, mac: MacAddress, ip: IPv4Address | None, at: datetime) -> Self:
        return cls(
            mac=mac, ip=ip, first_seen=at, last_seen=at, acknowledged=False, labels=NO_LABELS
        )

    def seen(self, ip: IPv4Address | None, at: datetime) -> Self:
        if at < self.last_seen:
            return self
        return replace(self, ip=ip or self.ip, last_seen=at)

    def acknowledge(self) -> Self:
        return replace(self, acknowledged=True)

    def relabel(self, labels: DeviceLabels) -> Self:
        return replace(self, labels=labels, acknowledged=True)
