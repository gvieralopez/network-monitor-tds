from collections.abc import Iterable
from ipaddress import IPv4Address

from scapy.layers.dhcp import BOOTP, DHCP
from scapy.packet import Packet

from network_monitor_tds.domain.network.models import MacAddress
from network_monitor_tds.domain.observations.models import KnownField
from network_monitor_tds.plugins.builtin.capture.models import Sighting

BOOT_REQUEST = 1
MAC_LENGTH = 6
OPTION_PAIR = 2
UNSPECIFIED = IPv4Address(0)

type DhcpOptions = dict[str, object]


def dhcp_sighting(packet: Packet) -> Sighting | None:
    if BOOTP not in packet or DHCP not in packet or packet[BOOTP].op != BOOT_REQUEST:
        return None
    options = _options(packet[DHCP].options)
    return Sighting(
        mac=MacAddress.parse(bytes(packet[BOOTP].chaddr)[:MAC_LENGTH].hex()),
        ip=_client_ip(options, IPv4Address(str(packet[BOOTP].ciaddr))),
        fields=_fields(options),
    )


def _options(raw: Iterable[object]) -> DhcpOptions:
    return {
        str(option[0]): option[1] if len(option) == OPTION_PAIR else list(option[1:])
        for option in raw
        if isinstance(option, tuple) and len(option) >= OPTION_PAIR
    }


def _client_ip(options: DhcpOptions, client_address: IPv4Address) -> IPv4Address | None:
    requested = options.get("requested_addr")
    if requested is not None:
        return IPv4Address(str(requested))
    return None if client_address == UNSPECIFIED else client_address


def _fields(options: DhcpOptions) -> dict[str, str]:
    fields = {
        KnownField.DHCP_HOSTNAME: _text(options.get("hostname")),
        KnownField.DHCP_VENDOR_CLASS: _text(options.get("vendor_class_id")),
        KnownField.DHCP_FINGERPRINT: _fingerprint(options.get("param_req_list")),
    }
    return {name: value for name, value in fields.items() if value}


def _text(value: object) -> str:
    if isinstance(value, bytes):
        return value.decode(errors="replace").strip("\x00 ")
    return str(value) if value is not None else ""


def _fingerprint(value: object) -> str:
    if isinstance(value, list | tuple):
        return ",".join(str(code) for code in value)
    if isinstance(value, bytes):
        return ",".join(str(code) for code in value)
    return ""
