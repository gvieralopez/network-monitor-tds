from ipaddress import IPv4Address

import pytest
from scapy.layers.dhcp import BOOTP, DHCP
from scapy.layers.inet import IP, UDP
from scapy.layers.l2 import Ether
from scapy.packet import Packet

from network_monitor_tds.domain.network.models import MacAddress
from network_monitor_tds.domain.observations.models import KnownField
from network_monitor_tds.plugins.builtin.capture.models import Sighting
from network_monitor_tds.plugins.builtin.dhcp.packets import dhcp_sighting

PIXEL = MacAddress.parse("3a:f1:5c:22:9b:07")


def dhcp(op: int, ciaddr: str, options: list[object]) -> Packet:
    return (
        Ether()
        / IP()
        / UDP(sport=68, dport=67)
        / BOOTP(op=op, chaddr=bytes.fromhex("3af15c229b07") + bytes(10), ciaddr=ciaddr)
        / DHCP(options=options)
    )


REQUEST = dhcp(
    1,
    "0.0.0.0",
    [
        ("message-type", "request"),
        ("requested_addr", "192.168.1.30"),
        ("hostname", b"Pixel-8"),
        ("vendor_class_id", b"android-dhcp-14"),
        ("param_req_list", [1, 3, 6, 15, 26, 28, 51, 58, 59, 43]),
        "end",
    ],
)


@pytest.mark.parametrize(
    ("packet", "expected"),
    [
        (
            REQUEST,
            Sighting(
                PIXEL,
                IPv4Address("192.168.1.30"),
                {
                    KnownField.DHCP_HOSTNAME: "Pixel-8",
                    KnownField.DHCP_VENDOR_CLASS: "android-dhcp-14",
                    KnownField.DHCP_FINGERPRINT: "1,3,6,15,26,28,51,58,59,43",
                },
            ),
        ),
        (
            dhcp(1, "192.168.1.30", [("message-type", "inform"), "end"]),
            Sighting(PIXEL, IPv4Address("192.168.1.30"), {}),
        ),
        (dhcp(1, "0.0.0.0", [("message-type", "discover"), "end"]), Sighting(PIXEL, None, {})),
        (dhcp(2, "0.0.0.0", [("message-type", "ack"), "end"]), None),
        (Ether() / IP() / UDP(), None),
    ],
)
def test_dhcp_sighting(packet: Packet, expected: Sighting | None) -> None:
    assert dhcp_sighting(packet) == expected
