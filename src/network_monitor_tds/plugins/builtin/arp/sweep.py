from ipaddress import IPv4Network

from scapy.layers.l2 import ARP, Ether
from scapy.sendrecv import srp

from network_monitor_tds.plugins.builtin.arp.packets import arp_sighting
from network_monitor_tds.plugins.builtin.capture.errors import CapturePermissionError
from network_monitor_tds.plugins.builtin.capture.models import Sighting

BROADCAST = "ff:ff:ff:ff:ff:ff"


def sweep(network: IPv4Network, interface: str, reply_timeout: float) -> list[Sighting]:
    request = Ether(dst=BROADCAST) / ARP(pdst=str(network))
    try:
        answered, _unanswered = srp(request, iface=interface, timeout=reply_timeout, verbose=False)
    except PermissionError as error:
        raise CapturePermissionError from error
    sightings = (arp_sighting(reply) for _request, reply in answered)
    return [sighting for sighting in sightings if sighting is not None]
