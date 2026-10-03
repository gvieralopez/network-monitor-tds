import asyncio
import logging
from collections.abc import AsyncGenerator

from scapy.config import conf
from scapy.packet import Packet
from scapy.sendrecv import AsyncSniffer

from network_monitor_tds.plugins.builtin.capture.errors import CapturePermissionError

logger = logging.getLogger(__name__)

QUEUE_SIZE = 1000


async def capture(bpf_filter: str, interface: str) -> AsyncGenerator[Packet]:
    loop = asyncio.get_running_loop()
    packets: asyncio.Queue[Packet] = asyncio.Queue(QUEUE_SIZE)
    try:
        socket = conf.L2listen(iface=interface, filter=bpf_filter)
    except PermissionError as error:
        raise CapturePermissionError from error

    def on_packet(packet: Packet) -> None:
        loop.call_soon_threadsafe(_offer, packets, packet)

    sniffer = AsyncSniffer(opened_socket=socket, store=False, prn=on_packet)
    sniffer.start()
    try:
        while True:
            yield await packets.get()
    finally:
        sniffer.stop(join=False)
        socket.close()


def _offer(packets: asyncio.Queue[Packet], packet: Packet) -> None:
    try:
        packets.put_nowait(packet)
    except asyncio.QueueFull:
        logger.warning("Capture queue is full; dropping a packet")
