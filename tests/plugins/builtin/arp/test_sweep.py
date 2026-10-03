from ipaddress import IPv4Address, IPv4Network

import pytest
from scapy.layers.l2 import ARP, Ether
from scapy.packet import Packet

from network_monitor_tds.domain.network.models import MacAddress
from network_monitor_tds.plugins.builtin.arp import sweep
from network_monitor_tds.plugins.builtin.capture.errors import CapturePermissionError
from network_monitor_tds.plugins.builtin.capture.models import Sighting

NETWORK = IPv4Network("192.168.1.0/24")


def test_sweep_returns_replies(monkeypatch: pytest.MonkeyPatch) -> None:
    sent: list[tuple[Packet, str, float]] = []
    reply = Ether() / ARP(op="is-at", hwsrc="24:0a:c4:9f:31:5e", psrc="192.168.1.143")
    junk = Ether() / ARP(hwsrc="00:00:00:00:00:00", psrc="192.168.1.9")

    def fake_srp(
        request: Packet, iface: str, timeout: float, verbose: bool
    ) -> tuple[list[tuple[Packet, Packet]], list[Packet]]:
        sent.append((request, iface, timeout))
        return [(request, reply), (request, junk)], []

    monkeypatch.setattr(sweep, "srp", fake_srp)

    assert sweep.sweep(NETWORK, "wlan0", 2.5) == [
        Sighting(MacAddress.parse("24:0a:c4:9f:31:5e"), IPv4Address("192.168.1.143"), {})
    ]
    request, iface, timeout = sent[0]
    assert (request[ARP].pdst, request[Ether].dst, iface, timeout) == (
        "192.168.1.0/24", "ff:ff:ff:ff:ff:ff", "wlan0", 2.5
    )  # fmt: skip


def test_sweep_without_permission(monkeypatch: pytest.MonkeyPatch) -> None:
    def refuse(*_args: object, **_kwargs: object) -> None:
        raise PermissionError

    monkeypatch.setattr(sweep, "srp", refuse)

    with pytest.raises(CapturePermissionError):
        sweep.sweep(NETWORK, "wlan0", 1)
