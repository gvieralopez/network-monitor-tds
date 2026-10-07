from ipaddress import IPv4Address, IPv4Network

from scapy.arch import get_if_addr, get_if_hwaddr
from scapy.config import conf
from scapy.route import Route

from network_monitor_tds.domain.network.models import MacAddress
from network_monitor_tds.plugins.builtin.capture.errors import UnknownNetworkError
from network_monitor_tds.plugins.builtin.capture.models import Sighting

UNSPECIFIED = str(IPv4Address(0))

HOST_PREFIX = 32


def resolve_interface(configured: str) -> str:
    return configured or str(_route_table().route(UNSPECIFIED)[0])


def refresh_routes() -> None:
    _route_table().resync()


def interface_placeholder() -> str:
    return f"{resolve_interface('')} (default route)"


def subnet_placeholder() -> str:
    interface = resolve_interface("")
    try:
        return f"{interface_network(interface)}, from {interface}"
    except UnknownNetworkError:
        return ""


def interface_network(interface: str) -> IPv4Network:
    for net, mask, gateway, route_interface, address, _metric in _route_table().routes:
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


def _route_table() -> Route:
    return conf.route
