from ipaddress import IPv4Address, IPv4Network

from scapy.arch import get_if_addr, get_if_hwaddr
from scapy.route import Route

from network_monitor_tds.domain.network.models import MacAddress
from network_monitor_tds.plugins.builtin.capture.errors import UnknownNetworkError
from network_monitor_tds.plugins.builtin.capture.models import Sighting

UNSPECIFIED = str(IPv4Address(0))

HOST_PREFIX = 32


def resolve_interface(configured: str) -> str:
    return configured or str(Route().route(UNSPECIFIED)[0])


def interface_network(interface: str) -> IPv4Network:
    for net, mask, gateway, route_interface, address, _metric in Route().routes:
        if route_interface != interface or gateway != UNSPECIFIED:
            continue
        network = IPv4Network(f"{IPv4Address(net)}/{IPv4Address(mask)}", strict=False)
        if 0 < network.prefixlen < HOST_PREFIX and IPv4Address(address) in network:
            return network
    raise UnknownNetworkError(interface)


def own_sighting(interface: str) -> Sighting:
    return Sighting(
        mac=MacAddress.parse(get_if_hwaddr(interface)),
        ip=IPv4Address(get_if_addr(interface)),
        fields={},
    )
