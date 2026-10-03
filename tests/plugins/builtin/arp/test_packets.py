from ipaddress import IPv4Address

import pytest
from scapy.layers.inet import IP, UDP
from scapy.layers.l2 import ARP, Ether
from scapy.packet import Packet

from network_monitor_tds.domain.network.models import MacAddress
from network_monitor_tds.plugins.builtin.arp.packets import arp_sighting
from network_monitor_tds.plugins.builtin.capture.models import Sighting

ESP = "24:0a:c4:9f:31:5e"


@pytest.mark.parametrize(
    ("packet", "expected"),
    [
        (
            Ether() / ARP(op="is-at", hwsrc=ESP, psrc="192.168.1.143"),
            Sighting(MacAddress.parse(ESP), IPv4Address("192.168.1.143"), {}),
        ),
        (
            Ether() / ARP(op="who-has", hwsrc=ESP, psrc="0.0.0.0", pdst="192.168.1.143"),
            Sighting(MacAddress.parse(ESP), None, {}),
        ),
        (Ether() / ARP(hwsrc="00:00:00:00:00:00", psrc="192.168.1.9"), None),
        (Ether() / ARP(hwsrc="01:00:5e:00:00:01", psrc="192.168.1.9"), None),
        (Ether() / IP() / UDP(), None),
    ],
)
def test_arp_sighting(packet: Packet, expected: Sighting | None) -> None:
    assert arp_sighting(packet) == expected
