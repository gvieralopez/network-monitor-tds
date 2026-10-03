from ipaddress import IPv4Address

from scapy.layers.l2 import ARP
from scapy.packet import Packet

from network_monitor_tds.domain.network.errors import InvalidMacAddressError
from network_monitor_tds.domain.network.models import MacAddress
from network_monitor_tds.plugins.builtin.capture.models import Sighting

UNSPECIFIED = IPv4Address(0)
ZERO_MAC = MacAddress("00:00:00:00:00:00")


def arp_sighting(packet: Packet) -> Sighting | None:
    if ARP not in packet:
        return None
    arp = packet[ARP]
    try:
        mac = MacAddress.parse(str(arp.hwsrc))
    except InvalidMacAddressError:
        return None
    if mac == ZERO_MAC or mac.is_multicast:
        return None
    ip = IPv4Address(str(arp.psrc))
    return Sighting(mac=mac, ip=None if ip == UNSPECIFIED else ip, fields={})
