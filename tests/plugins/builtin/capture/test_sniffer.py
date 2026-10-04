import asyncio
import logging
from collections.abc import Callable

import pytest
from scapy.config import conf
from scapy.layers.inet import UDP
from scapy.layers.l2 import ARP, Ether
from scapy.packet import Packet

from network_monitor_tds.plugins.builtin.capture import sniffer
from network_monitor_tds.plugins.builtin.capture.errors import CapturePermissionError
from network_monitor_tds.plugins.builtin.capture.models import PacketFilter
from network_monitor_tds.plugins.builtin.capture.sniffer import CaptureHub, capture

pytestmark = pytest.mark.anyio

ARP_ONLY = PacketFilter("arp", lambda packet: ARP in packet)
UDP_ONLY = PacketFilter("udp", lambda packet: UDP in packet)
ARP_PACKET = Ether() / ARP(psrc="192.168.1.20")
UDP_PACKET = Ether() / UDP(sport=68, dport=67)


class FakeSocket:
    def __init__(self, interface: str, bpf: str) -> None:
        self.interface = interface
        self.bpf = bpf
        self.closed = False
        self.sniffer: FakeSniffer | None = None

    def deliver(self, packet: Packet) -> None:
        assert self.sniffer is not None
        assert self.sniffer.prn(packet) is None, "scapy prints whatever prn returns"

    def close(self) -> None:
        self.closed = True


class FakeSniffer:
    def __init__(
        self, opened_socket: FakeSocket, store: bool, prn: Callable[[Packet], None]
    ) -> None:
        self.prn = prn
        self.running = False
        opened_socket.sniffer = self

    def start(self) -> None:
        self.running = True

    def stop(self, join: bool) -> None:
        self.running = False


@pytest.fixture
def sockets(monkeypatch: pytest.MonkeyPatch) -> list[FakeSocket]:
    opened: list[FakeSocket] = []

    def listen(**options: str) -> FakeSocket:
        opened.append(FakeSocket(options["iface"], options["filter"]))
        return opened[-1]

    monkeypatch.setattr(conf, "L2listen", listen)
    monkeypatch.setattr(sniffer, "AsyncSniffer", FakeSniffer)
    return opened


async def test_capture_shares_one_hub_per_interface(sockets: list[FakeSocket]) -> None:
    arp = capture(ARP_ONLY, "test-shared")
    udp = capture(UDP_ONLY, "test-shared")
    other = capture(ARP_ONLY, "test-other")
    pending = [asyncio.ensure_future(anext(stream)) for stream in (arp, udp, other)]
    await asyncio.sleep(0)

    assert [(s.interface, s.bpf) for s in sockets] == [
        ("test-shared", "(arp)"),
        ("test-shared", "(arp) or (udp)"),
        ("test-other", "(arp)"),
    ]
    sockets[-1].deliver(ARP_PACKET)
    assert await pending[-1] == ARP_PACKET
    for task in pending[:-1]:
        task.cancel()
    await asyncio.gather(*pending, return_exceptions=True)
    await other.aclose()


async def test_hub_fans_packets_out_by_filter(sockets: list[FakeSocket]) -> None:
    hub = CaptureHub("wlan0")
    arp, udp = hub.packets(ARP_ONLY), hub.packets(UDP_ONLY)
    next_arp, next_udp = asyncio.ensure_future(anext(arp)), asyncio.ensure_future(anext(udp))
    await asyncio.sleep(0)

    sockets[-1].deliver(UDP_PACKET)
    sockets[-1].deliver(ARP_PACKET)

    assert (await next_arp, await next_udp) == (ARP_PACKET, UDP_PACKET)
    assert [socket.closed for socket in sockets] == [True, False]
    await arp.aclose()
    await udp.aclose()


async def test_hub_narrows_then_stops_as_subscribers_leave(
    sockets: list[FakeSocket], caplog: pytest.LogCaptureFixture
) -> None:
    hub = CaptureHub("wlan0")
    arp, udp = hub.packets(ARP_ONLY), hub.packets(UDP_ONLY)
    next_arp, next_udp = asyncio.ensure_future(anext(arp)), asyncio.ensure_future(anext(udp))
    await asyncio.sleep(0)
    sockets[-1].deliver(ARP_PACKET)
    sockets[-1].deliver(UDP_PACKET)
    await asyncio.gather(next_arp, next_udp)

    await udp.aclose()
    narrowed = sockets[-1]
    with caplog.at_level(logging.INFO):
        await arp.aclose()

    assert narrowed.bpf == "(arp)"
    assert all(socket.closed for socket in sockets)
    assert not any(socket.sniffer and socket.sniffer.running for socket in sockets)
    assert "Stopped capturing on wlan0" in caplog.text


async def test_hub_ignores_subscribers_with_a_filter_already_captured(
    sockets: list[FakeSocket],
) -> None:
    hub = CaptureHub("wlan0")
    first, second = hub.packets(ARP_ONLY), hub.packets(ARP_ONLY)
    pending = [asyncio.ensure_future(anext(first)), asyncio.ensure_future(anext(second))]
    await asyncio.sleep(0)

    sockets[-1].deliver(ARP_PACKET)

    assert await asyncio.gather(*pending) == [ARP_PACKET, ARP_PACKET]
    assert len(sockets) == 1
    await first.aclose()
    await second.aclose()


async def test_hub_without_permission_keeps_the_running_capture(
    sockets: list[FakeSocket], monkeypatch: pytest.MonkeyPatch
) -> None:
    hub = CaptureHub("wlan0")
    arp = hub.packets(ARP_ONLY)
    next_arp = asyncio.ensure_future(anext(arp))
    await asyncio.sleep(0)

    def refuse(**_options: str) -> FakeSocket:
        raise PermissionError

    monkeypatch.setattr(conf, "L2listen", refuse)

    with pytest.raises(CapturePermissionError, match="CAP_NET_RAW"):
        await anext(hub.packets(UDP_ONLY))
    sockets[-1].deliver(UDP_PACKET)
    sockets[-1].deliver(ARP_PACKET)
    assert await next_arp == ARP_PACKET
    assert not sockets[-1].closed
    await arp.aclose()


async def test_hub_keeps_the_wider_capture_when_narrowing_fails(
    sockets: list[FakeSocket], monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    hub = CaptureHub("wlan0")
    arp, udp = hub.packets(ARP_ONLY), hub.packets(UDP_ONLY)
    next_arp, next_udp = asyncio.ensure_future(anext(arp)), asyncio.ensure_future(anext(udp))
    await asyncio.sleep(0)
    sockets[-1].deliver(ARP_PACKET)
    sockets[-1].deliver(UDP_PACKET)
    await asyncio.gather(next_arp, next_udp)

    def fail(**_options: str) -> FakeSocket:
        raise OSError

    monkeypatch.setattr(conf, "L2listen", fail)
    with caplog.at_level(logging.ERROR):
        await udp.aclose()

    assert "Could not narrow the capture on wlan0" in caplog.text
    assert (sockets[-1].bpf, sockets[-1].closed) == ("(arp) or (udp)", False)
    next_arp = asyncio.ensure_future(anext(arp))
    sockets[-1].deliver(ARP_PACKET)
    assert await next_arp == ARP_PACKET
    await arp.aclose()


async def test_hub_drops_packets_when_a_subscriber_falls_behind(
    sockets: list[FakeSocket], monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    monkeypatch.setattr(sniffer, "QUEUE_SIZE", 1)
    hub = CaptureHub("wlan0")
    arp = hub.packets(ARP_ONLY)
    next_arp = asyncio.ensure_future(anext(arp))
    await asyncio.sleep(0)
    sockets[-1].deliver(ARP_PACKET)
    await next_arp

    with caplog.at_level(logging.WARNING):
        sockets[-1].deliver(ARP_PACKET)
        sockets[-1].deliver(ARP_PACKET)
        await asyncio.sleep(0)

    assert "Capture queue is full" in caplog.text
    await arp.aclose()
