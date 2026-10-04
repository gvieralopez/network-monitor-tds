import logging
from collections.abc import AsyncIterator, Sequence
from dataclasses import replace
from datetime import timedelta
from ipaddress import IPv4Address, IPv4Network

import pytest
from pydantic import ValidationError
from scapy.layers.l2 import ARP, Ether
from scapy.packet import Packet

from network_monitor_tds.domain.network.models import MacAddress
from network_monitor_tds.domain.observations.models import ObservationKind
from network_monitor_tds.domain.plugins.models import PluginId
from network_monitor_tds.plugins.builtin.arp import plugin
from network_monitor_tds.plugins.builtin.arp.packets import ARP_FILTER
from network_monitor_tds.plugins.builtin.arp.plugin import (
    ArpListenerPlugin,
    ArpListenerSettings,
    ArpSweepPlugin,
    ArpSweepSettings,
)
from network_monitor_tds.plugins.builtin.arp.sweep import SweepTargets
from network_monitor_tds.plugins.builtin.capture.errors import NetworkTooLargeError
from network_monitor_tds.plugins.builtin.capture.models import PacketFilter, Sighting
from network_monitor_tds.plugins.sdk.base import PluginContext
from network_monitor_tds.plugins.sdk.models import KnownDevice
from tests.conftest import T0, FixedClock, RecordingEmit, plugin_context

pytestmark = pytest.mark.anyio

SELF = Sighting(MacAddress.parse("04:68:74:5c:e3:fb"), IPv4Address("192.168.1.107"), {})
ESP = Sighting(MacAddress.parse("24:0a:c4:9f:31:5e"), IPv4Address("192.168.1.143"), {})
LAN = IPv4Network("192.168.1.0/24")
QUIET_TV = KnownDevice(
    MacAddress.parse("a4:77:33:12:9e:01"), IPv4Address("192.168.1.30"), T0 - timedelta(minutes=6)
)
CHATTY_PHONE = KnownDevice(
    MacAddress.parse("3c:28:6d:aa:10:02"), IPv4Address("192.168.1.31"), T0 - timedelta(minutes=1)
)


@pytest.fixture
def swept(monkeypatch: pytest.MonkeyPatch) -> list[SweepTargets]:
    targets: list[SweepTargets] = []

    def fake_sweep(asked: SweepTargets, interface: str, timeout: float) -> list[Sighting]:
        targets.append(asked)
        return [ESP]

    monkeypatch.setattr(plugin, "resolve_interface", lambda configured: configured or "wlan0")
    monkeypatch.setattr(plugin, "interface_network", lambda _name: LAN)
    monkeypatch.setattr(plugin, "own_sighting", lambda _name: SELF)
    monkeypatch.setattr(plugin, "sweep", fake_sweep)
    return targets


async def test_sweep_reports_replies_and_itself(swept: list[SweepTargets]) -> None:
    emit = RecordingEmit()

    await ArpSweepPlugin(ArpSweepSettings()).run(plugin_context("arp-sweep", emit))

    assert [(o.mac, o.ip, o.kind) for o in emit.observations] == [
        (SELF.mac, SELF.ip, ObservationKind.SIGHTING),
        (ESP.mac, ESP.ip, ObservationKind.SIGHTING),
    ]
    assert swept == [LAN]


async def test_sweep_uses_configured_subnet(swept: list[SweepTargets]) -> None:
    settings = ArpSweepSettings(subnet="10.0.0.0/28")

    await ArpSweepPlugin(settings).run(plugin_context("arp-sweep", RecordingEmit()))

    assert swept == [IPv4Network("10.0.0.0/28")]


@pytest.mark.usefixtures("swept")
async def test_sweep_refuses_large_networks() -> None:
    settings = ArpSweepSettings(subnet="10.0.0.0/16")

    with pytest.raises(NetworkTooLargeError, match="65536"):
        await ArpSweepPlugin(settings).run(plugin_context("arp-sweep", RecordingEmit()))


@pytest.mark.parametrize(
    ("minutes", "asked"),
    [
        ([0, 5, 10], [LAN, [QUIET_TV.ip], [QUIET_TV.ip]]),
        ([0, 5, 30, 35], [LAN, [QUIET_TV.ip], LAN, [QUIET_TV.ip]]),
    ],
)
async def test_sweep_asks_quiet_devices_between_full_sweeps(
    swept: list[SweepTargets], minutes: list[int], asked: list[SweepTargets]
) -> None:
    sweeper = ArpSweepPlugin(ArpSweepSettings())

    for minute in minutes:
        await sweeper.run(_context(minute, [QUIET_TV, CHATTY_PHONE], RecordingEmit()))

    assert swept == asked


@pytest.mark.parametrize(("minutes_ago", "asked"), [(3, True), (2, False)])
async def test_sweep_counts_devices_quiet_after_half_an_interval(
    swept: list[SweepTargets], minutes_ago: int, asked: bool
) -> None:
    device = replace(QUIET_TV, last_seen=T0 - timedelta(minutes=minutes_ago))
    sweeper = ArpSweepPlugin(ArpSweepSettings(interval=timedelta(minutes=5)))
    await sweeper.run(_context(0, [], RecordingEmit()))

    await sweeper.run(_context(0, [device], RecordingEmit()))

    assert swept == ([LAN, [QUIET_TV.ip]] if asked else [LAN])


async def test_sweep_without_quiet_devices_only_reports_itself(swept: list[SweepTargets]) -> None:
    sweeper = ArpSweepPlugin(ArpSweepSettings())
    await sweeper.run(_context(0, [], RecordingEmit()))
    emit = RecordingEmit()

    await sweeper.run(_context(5, [CHATTY_PHONE], emit))

    assert swept == [LAN]
    assert [observation.mac for observation in emit.observations] == [SELF.mac]


async def test_failed_full_sweep_is_retried(
    swept: list[SweepTargets], monkeypatch: pytest.MonkeyPatch
) -> None:
    sweeper = ArpSweepPlugin(ArpSweepSettings())

    def broken_sweep(asked: SweepTargets, interface: str, timeout: float) -> list[Sighting]:
        raise OSError

    with monkeypatch.context() as patch:
        patch.setattr(plugin, "sweep", broken_sweep)
        with pytest.raises(OSError):
            await sweeper.run(_context(0, [QUIET_TV], RecordingEmit()))
    await sweeper.run(_context(5, [QUIET_TV], RecordingEmit()))

    assert swept == [LAN]


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


def _context(minute: int, devices: Sequence[KnownDevice], emit: RecordingEmit) -> PluginContext:
    elapsed = timedelta(minutes=minute)

    async def known_devices() -> Sequence[KnownDevice]:
        return [replace(device, last_seen=device.last_seen + elapsed) for device in devices]

    clock = FixedClock(T0 + elapsed)
    return PluginContext(
        PluginId("arp-sweep"), clock, emit, logging.getLogger("tests.arp-sweep"), known_devices
    )
