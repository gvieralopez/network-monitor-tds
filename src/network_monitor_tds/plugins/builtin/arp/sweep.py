from collections.abc import Iterable, Sequence
from datetime import datetime
from ipaddress import IPv4Address, IPv4Network

from scapy.layers.l2 import ARP, Ether
from scapy.sendrecv import srp

from network_monitor_tds.plugins.builtin.arp.packets import arp_sighting
from network_monitor_tds.plugins.builtin.capture.errors import CapturePermissionError
from network_monitor_tds.plugins.builtin.capture.models import Sighting
from network_monitor_tds.plugins.sdk.models import KnownDevice

BROADCAST = "ff:ff:ff:ff:ff:ff"

type SweepTargets = IPv4Network | Sequence[IPv4Address]


def sweep(targets: SweepTargets, interface: str, reply_timeout: float) -> list[Sighting]:
    destinations = str(targets) if isinstance(targets, IPv4Network) else [str(ip) for ip in targets]
    request = Ether(dst=BROADCAST) / ARP(pdst=destinations)
    try:
        answered, _unanswered = srp(request, iface=interface, timeout=reply_timeout, verbose=False)
    except PermissionError as error:
        raise CapturePermissionError from error
    sightings = (arp_sighting(reply) for _request, reply in answered)
    return [sighting for sighting in sightings if sighting is not None]


def target_count(targets: SweepTargets) -> int:
    return targets.num_addresses if isinstance(targets, IPv4Network) else len(targets)


def quiet_addresses(
    devices: Iterable[KnownDevice],
    network: IPv4Network,
    quiet_since: datetime,
    gone_since: datetime,
) -> list[IPv4Address]:
    return sorted(
        {
            device.ip
            for device in devices
            if device.ip is not None
            and device.ip in network
            and gone_since <= device.last_seen < quiet_since
        }
    )
