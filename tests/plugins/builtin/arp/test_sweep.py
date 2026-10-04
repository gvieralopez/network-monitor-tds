from datetime import timedelta
from ipaddress import IPv4Address, IPv4Network

import pytest
from scapy.layers.l2 import ARP, Ether
from scapy.packet import Packet

from network_monitor_tds.domain.network.models import MacAddress
from network_monitor_tds.plugins.builtin.arp import sweep
from network_monitor_tds.plugins.builtin.arp.sweep import SweepTargets
from network_monitor_tds.plugins.builtin.capture.errors import CapturePermissionError
from network_monitor_tds.plugins.builtin.capture.models import Sighting
from network_monitor_tds.plugins.sdk.models import KnownDevice
from tests.conftest import T0

NETWORK = IPv4Network("192.168.1.0/24")
TV = IPv4Address("192.168.1.30")
PHONE = IPv4Address("192.168.1.31")


@pytest.mark.parametrize(
    ("targets", "pdst"),
    [(NETWORK, "192.168.1.0/24"), ([TV, PHONE], ["192.168.1.30", "192.168.1.31"])],
)
def test_sweep_returns_replies(
    monkeypatch: pytest.MonkeyPatch, targets: SweepTargets, pdst: str | list[str]
) -> None:
    sent: list[tuple[Packet, str, float]] = []
    reply = Ether() / ARP(op="is-at", hwsrc="24:0a:c4:9f:31:5e", psrc="192.168.1.143")
    junk = Ether() / ARP(hwsrc="00:00:00:00:00:00", psrc="192.168.1.9")

    def fake_srp(
        request: Packet, iface: str, timeout: float, verbose: bool
    ) -> tuple[list[tuple[Packet, Packet]], list[Packet]]:
        sent.append((request, iface, timeout))
        return [(request, reply), (request, junk)], []

    monkeypatch.setattr(sweep, "srp", fake_srp)

    assert sweep.sweep(targets, "wlan0", 2.5) == [
        Sighting(MacAddress.parse("24:0a:c4:9f:31:5e"), IPv4Address("192.168.1.143"), {})
    ]
    request, iface, timeout = sent[0]
    assert (request[ARP].pdst, request[Ether].dst, iface, timeout) == (
        pdst, "ff:ff:ff:ff:ff:ff", "wlan0", 2.5
    )  # fmt: skip


def test_sweep_without_permission(monkeypatch: pytest.MonkeyPatch) -> None:
    def refuse(*_args: object, **_kwargs: object) -> None:
        raise PermissionError

    monkeypatch.setattr(sweep, "srp", refuse)

    with pytest.raises(CapturePermissionError):
        sweep.sweep(NETWORK, "wlan0", 1)


@pytest.mark.parametrize(
    ("ip", "minutes_ago", "asked"),
    [
        (TV, 6, True),
        (TV, 4, False),
        (TV, 30, True),
        (TV, 31, False),
        (IPv4Address("10.0.0.5"), 6, False),
        (None, 6, False),
    ],
)
def test_quiet_addresses(ip: IPv4Address | None, minutes_ago: int, asked: bool) -> None:
    device = KnownDevice(
        MacAddress.parse("a4:77:33:12:9e:01"), ip, T0 - timedelta(minutes=minutes_ago)
    )

    addresses = sweep.quiet_addresses(
        [device], NETWORK, T0 - timedelta(minutes=5), T0 - timedelta(minutes=30)
    )

    assert addresses == ([ip] if asked else [])


def test_quiet_addresses_are_sorted_and_unique() -> None:
    devices = [
        KnownDevice(MacAddress.parse(f"a4:77:33:12:9e:0{index}"), ip, T0 - timedelta(minutes=6))
        for index, ip in enumerate([PHONE, TV, PHONE])
    ]

    addresses = sweep.quiet_addresses(devices, NETWORK, T0, T0 - timedelta(minutes=30))

    assert addresses == [TV, PHONE]


@pytest.mark.parametrize(("targets", "count"), [(NETWORK, 256), ([TV, PHONE], 2), ([], 0)])
def test_target_count(targets: SweepTargets, count: int) -> None:
    assert sweep.target_count(targets) == count
