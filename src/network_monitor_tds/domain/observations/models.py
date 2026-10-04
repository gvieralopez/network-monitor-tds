from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from ipaddress import IPv4Address

from network_monitor_tds.domain.network.models import MacAddress
from network_monitor_tds.domain.plugins.models import PluginId
from network_monitor_tds.domain.time import ensure_aware


class KnownField(StrEnum):
    LEASE_HOSTNAME = "lease_hostname"
    DHCP_HOSTNAME = "dhcp_hostname"
    DHCP_VENDOR_CLASS = "dhcp_vendor_class"
    DHCP_FINGERPRINT = "dhcp_fingerprint"
    MDNS_NAME = "mdns_name"
    MDNS_SERVICES = "mdns_services"
    UPNP_FRIENDLY_NAME = "upnp_friendly_name"
    UPNP_MODEL = "upnp_model"
    VENDOR = "vendor"
    OPEN_PORTS = "open_ports"


class ObservationKind(StrEnum):
    SIGHTING = "sighting"
    ENRICHMENT = "enrichment"


@dataclass(frozen=True, slots=True)
class Observation:
    source: PluginId
    kind: ObservationKind
    mac: MacAddress
    ip: IPv4Address | None
    observed_at: datetime
    fields: Mapping[str, str]

    def __post_init__(self) -> None:
        ensure_aware(self.observed_at)


@dataclass(frozen=True, slots=True)
class Fact:
    name: str
    value: str
    source: PluginId
    observed_at: datetime

    def __post_init__(self) -> None:
        ensure_aware(self.observed_at)


@dataclass(frozen=True, slots=True)
class Detection:
    source: PluginId
    first_seen: datetime
    last_seen: datetime

    def __post_init__(self) -> None:
        ensure_aware(self.first_seen)
        ensure_aware(self.last_seen)
