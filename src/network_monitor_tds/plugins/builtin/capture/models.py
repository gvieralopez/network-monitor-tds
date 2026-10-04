from collections.abc import Callable, Mapping
from dataclasses import dataclass
from ipaddress import IPv4Address

from scapy.packet import Packet

from network_monitor_tds.domain.network.models import MacAddress


@dataclass(frozen=True, slots=True)
class Sighting:
    mac: MacAddress
    ip: IPv4Address | None
    fields: Mapping[str, str]


@dataclass(frozen=True, slots=True)
class PacketFilter:
    bpf: str
    matches: Callable[[Packet], bool]
