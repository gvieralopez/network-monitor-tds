from ipaddress import IPv4Address, IPv4Network

import pytest
from scapy.config import conf

from network_monitor_tds.domain.network.models import MacAddress
from network_monitor_tds.plugins.builtin.capture import interfaces
from network_monitor_tds.plugins.builtin.capture.errors import UnknownNetworkError
from network_monitor_tds.plugins.builtin.capture.models import Sighting


def address(text: str) -> int:
    return int(IPv4Address(text))


ROUTES = [
    (address("127.0.0.0"), address("255.0.0.0"), "0.0.0.0", "lo", "127.0.0.1", 0),
    (address("192.168.1.107"), address("255.255.255.255"), "0.0.0.0", "wlan0", "192.168.1.107", 0),
    (address("0.0.0.0"), address("0.0.0.0"), "192.168.1.1", "wlan0", "192.168.1.107", 600),
    (address("224.0.0.0"), address("240.0.0.0"), "0.0.0.0", "wlan0", "192.168.1.107", 250),
    (address("192.168.1.0"), address("255.255.255.0"), "0.0.0.0", "wlan0", "192.168.1.107", 600),
]  # fmt: skip


class FakeRoute:
    def __init__(self) -> None:
        self.routes = ROUTES
        self.resyncs = 0

    def route(self, _destination: str) -> tuple[str, str, str]:
        return ("wlan0", "192.168.1.107", "192.168.1.1")

    def resync(self) -> None:
        self.resyncs += 1


@pytest.fixture(autouse=True)
def fake_routes(monkeypatch: pytest.MonkeyPatch) -> FakeRoute:
    table = FakeRoute()
    monkeypatch.setattr(conf, "route", table)
    return table


@pytest.mark.parametrize(("configured", "resolved"), [("", "wlan0"), ("eth1", "eth1")])
def test_resolve_interface(configured: str, resolved: str) -> None:
    assert interfaces.resolve_interface(configured) == resolved


def test_interface_network_finds_connected_subnet() -> None:
    assert interfaces.interface_network("wlan0") == IPv4Network("192.168.1.0/24")


def test_interface_network_without_subnet_fails() -> None:
    with pytest.raises(UnknownNetworkError, match="eth9"):
        interfaces.interface_network("eth9")


def test_refresh_routes_resyncs_the_cached_table(fake_routes: FakeRoute) -> None:
    interfaces.refresh_routes()

    assert fake_routes.resyncs == 1


def test_own_sighting(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(interfaces, "get_if_hwaddr", lambda _name: "04:68:74:5c:e3:fb")
    monkeypatch.setattr(interfaces, "get_if_addr", lambda _name: "192.168.1.107")

    assert interfaces.own_sighting("wlan0") == Sighting(
        MacAddress.parse("04:68:74:5c:e3:fb"), IPv4Address("192.168.1.107"), {}
    )


def test_placeholders_name_the_default_interface_and_its_subnet() -> None:
    assert interfaces.interface_placeholder() == "wlan0 (default route)"
    assert interfaces.subnet_placeholder() == "192.168.1.0/24, from wlan0"


def test_subnet_placeholder_is_empty_without_a_subnet(fake_routes: FakeRoute) -> None:
    fake_routes.routes = []

    assert interfaces.subnet_placeholder() == ""
