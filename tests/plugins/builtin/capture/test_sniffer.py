from collections.abc import Callable

import pytest
from scapy.config import conf
from scapy.layers.l2 import ARP, Ether
from scapy.packet import Packet

from network_monitor_tds.plugins.builtin.capture import sniffer
from network_monitor_tds.plugins.builtin.capture.errors import CapturePermissionError

pytestmark = pytest.mark.anyio

PACKETS = [Ether() / ARP(psrc="192.168.1.20"), Ether() / ARP(psrc="192.168.1.21")]


class FakeSocket:
    closed = False

    def close(self) -> None:
        FakeSocket.closed = True


class FakeSniffer:
    stopped = False

    def __init__(
        self, opened_socket: FakeSocket, store: bool, prn: Callable[[Packet], None]
    ) -> None:
        self._prn = prn

    def start(self) -> None:
        for packet in PACKETS:
            assert self._prn(packet) is None, "scapy prints whatever prn returns"

    def stop(self, join: bool) -> None:
        FakeSniffer.stopped = True


async def test_capture_bridges_packets_and_cleans_up(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(conf, "L2listen", lambda **_options: FakeSocket())
    monkeypatch.setattr(sniffer, "AsyncSniffer", FakeSniffer)

    stream = sniffer.capture("arp", "wlan0")
    received = [await anext(stream), await anext(stream)]
    await stream.aclose()

    assert [packet[ARP].psrc for packet in received] == ["192.168.1.20", "192.168.1.21"]
    assert FakeSniffer.stopped and FakeSocket.closed


async def test_capture_without_permission(monkeypatch: pytest.MonkeyPatch) -> None:
    def refuse(**_options: str) -> FakeSocket:
        raise PermissionError

    monkeypatch.setattr(conf, "L2listen", refuse)

    with pytest.raises(CapturePermissionError, match="CAP_NET_RAW"):
        await anext(sniffer.capture("arp", "wlan0"))
