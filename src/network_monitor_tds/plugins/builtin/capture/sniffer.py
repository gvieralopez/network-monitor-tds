import asyncio
import logging
from collections.abc import AsyncGenerator, Iterable
from dataclasses import dataclass

from scapy.config import conf
from scapy.packet import Packet
from scapy.sendrecv import AsyncSniffer
from scapy.supersocket import SuperSocket

from network_monitor_tds.plugins.builtin.capture.errors import CapturePermissionError
from network_monitor_tds.plugins.builtin.capture.models import PacketFilter

logger = logging.getLogger(__name__)

QUEUE_SIZE = 1000


async def capture(packet_filter: PacketFilter, interface: str) -> AsyncGenerator[Packet]:
    hub = _HUBS.get(interface)
    if hub is None:
        hub = _HUBS[interface] = CaptureHub(interface)
    async for packet in hub.packets(packet_filter):
        yield packet


class CaptureHub:
    def __init__(self, interface: str) -> None:
        self._interface = interface
        self._subscribers: list[_Subscriber] = []
        self._bpf = ""
        self._running: _RunningCapture | None = None

    async def packets(self, packet_filter: PacketFilter) -> AsyncGenerator[Packet]:
        subscriber = _Subscriber(packet_filter, asyncio.Queue(QUEUE_SIZE))
        self._subscribers.append(subscriber)
        try:
            self._refresh()
        except BaseException:
            self._subscribers.remove(subscriber)
            raise
        try:
            while True:
                yield await subscriber.queue.get()
        finally:
            self._subscribers.remove(subscriber)
            self._narrow()

    def _narrow(self) -> None:
        try:
            self._refresh()
        except OSError:
            logger.exception("Could not narrow the capture on %s; keeping it", self._interface)

    def _refresh(self) -> None:
        bpf = _combined(subscriber.packet_filter.bpf for subscriber in self._subscribers)
        if bpf == self._bpf:
            return
        running = self._start(bpf) if bpf else None
        if self._running is not None:
            self._running.stop()
        self._bpf, self._running = bpf, running
        if bpf:
            logger.info("Capturing on %s with filter %r", self._interface, bpf)
        else:
            logger.info("Stopped capturing on %s", self._interface)

    def _start(self, bpf: str) -> _RunningCapture:
        loop = asyncio.get_running_loop()
        try:
            socket = conf.L2listen(iface=self._interface, filter=bpf)
        except PermissionError as error:
            raise CapturePermissionError from error

        def on_packet(packet: Packet) -> None:
            loop.call_soon_threadsafe(self._dispatch, packet)

        sniffer = AsyncSniffer(opened_socket=socket, store=False, prn=on_packet)
        sniffer.start()
        return _RunningCapture(socket, sniffer)

    def _dispatch(self, packet: Packet) -> None:
        for subscriber in self._subscribers:
            if subscriber.packet_filter.matches(packet):
                _offer(subscriber.queue, packet)


@dataclass(frozen=True, slots=True)
class _Subscriber:
    packet_filter: PacketFilter
    queue: asyncio.Queue[Packet]


@dataclass(frozen=True, slots=True)
class _RunningCapture:
    socket: SuperSocket
    sniffer: AsyncSniffer

    def stop(self) -> None:
        # scapy never closes a socket it was given; closing it before the sniffer thread exits
        # makes that thread read from a closed socket and log a warning.
        self.sniffer.stop(join=True)
        self.socket.close()


_HUBS: dict[str, CaptureHub] = {}


def _combined(filters: Iterable[str]) -> str:
    return " or ".join(f"({bpf})" for bpf in sorted(set(filters)))


def _offer(packets: asyncio.Queue[Packet], packet: Packet) -> None:
    try:
        packets.put_nowait(packet)
    except asyncio.QueueFull:
        logger.warning("Capture queue is full; dropping a packet")
