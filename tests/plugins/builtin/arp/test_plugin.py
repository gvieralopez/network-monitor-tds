from collections.abc import AsyncIterator
from datetime import timedelta
from ipaddress import IPv4Address, IPv4Network

import pytest
from pydantic import ValidationError
from scapy.layers.l2 import ARP, Ether
from scapy.packet import Packet

from network_monitor_tds.domain.network.models import MacAddress
from network_monitor_tds.domain.observations.models import ObservationKind
from network_monitor_tds.plugins.builtin.arp import plugin
from network_monitor_tds.plugins.builtin.arp.packets import ARP_FILTER
from network_monitor_tds.plugins.builtin.arp.plugin import (
    ArpListenerPlugin,
    ArpListenerSettings,
    ArpSweepPlugin,
    ArpSweepSettings,
)
from network_monitor_tds.plugins.builtin.capture.errors import NetworkTooLargeError
from network_monitor_tds.plugins.builtin.capture.models import PacketFilter, Sighting
from tests.conftest import RecordingEmit, plugin_context

pytestmark = pytest.mark.anyio

SELF = Sighting(MacAddress.parse("04:68:74:5c:e3:fb"), IPv4Address("192.168.1.107"), {})
ESP = Sighting(MacAddress.parse("24:0a:c4:9f:31:5e"), IPv4Address("192.168.1.143"), {})


@pytest.fixture
def swept(monkeypatch: pytest.MonkeyPatch) -> list[IPv4Network]:
    networks: list[IPv4Network] = []

    def fake_sweep(network: IPv4Network, interface: str, timeout: float) -> list[Sighting]:
        networks.append(network)
        return [ESP]

    monkeypatch.setattr(plugin, "resolve_interface", lambda configured: configured or "wlan0")
    monkeypatch.setattr(plugin, "interface_network", lambda _name: IPv4Network("192.168.1.0/24"))
    monkeypatch.setattr(plugin, "own_sighting", lambda _name: SELF)
    monkeypatch.setattr(plugin, "sweep", fake_sweep)
    return networks


async def test_sweep_reports_replies_and_itself(swept: list[IPv4Network]) -> None:
    emit = RecordingEmit()

    await ArpSweepPlugin(ArpSweepSettings()).run(plugin_context("arp-sweep", emit))

    assert [(o.mac, o.ip, o.kind) for o in emit.observations] == [
        (SELF.mac, SELF.ip, ObservationKind.SIGHTING),
        (ESP.mac, ESP.ip, ObservationKind.SIGHTING),
    ]
    assert swept == [IPv4Network("192.168.1.0/24")]


async def test_sweep_uses_configured_subnet(swept: list[IPv4Network]) -> None:
    settings = ArpSweepSettings(subnet="10.0.0.0/28")

    await ArpSweepPlugin(settings).run(plugin_context("arp-sweep", RecordingEmit()))

    assert swept == [IPv4Network("10.0.0.0/28")]


@pytest.mark.usefixtures("swept")
async def test_sweep_refuses_large_networks() -> None:
    settings = ArpSweepSettings(subnet="10.0.0.0/16")

    with pytest.raises(NetworkTooLargeError, match="65536"):
        await ArpSweepPlugin(settings).run(plugin_context("arp-sweep", RecordingEmit()))


def test_sweep_settings_reject_invalid_subnet() -> None:
    with pytest.raises(ValidationError):
        ArpSweepSettings(subnet="192.168.1.0/33")


async def test_listener_reports_throttled_sightings(monkeypatch: pytest.MonkeyPatch) -> None:
    packets = [
        Ether() / ARP(hwsrc=str(ESP.mac), psrc="192.168.1.143"),
        Ether() / ARP(hwsrc=str(ESP.mac), psrc="192.168.1.143"),
        Ether() / ARP(hwsrc="00:00:00:00:00:00", psrc="192.168.1.9"),
        Ether() / ARP(hwsrc=str(SELF.mac), psrc="192.168.1.107"),
    ]

    async def fake_capture(packet_filter: PacketFilter, interface: str) -> AsyncIterator[Packet]:
        assert (packet_filter, interface) == (ARP_FILTER, "eth1")
        for packet in packets:
            yield packet

    monkeypatch.setattr(plugin, "capture", fake_capture)
    monkeypatch.setattr(plugin, "resolve_interface", lambda configured: configured)
    emit = RecordingEmit()
    settings = ArpListenerSettings(interface="eth1", report_every=timedelta(minutes=1))

    await ArpListenerPlugin(settings).listen(plugin_context("arp-listen", emit))

    assert [observation.mac for observation in emit.observations] == [ESP.mac, SELF.mac]
