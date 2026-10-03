import asyncio
import logging
from collections.abc import AsyncGenerator

from network_monitor_tds.domain.events.models import DeviceEvent

logger = logging.getLogger(__name__)


class InMemoryEventBus:
    def __init__(self, capacity: int) -> None:
        self._capacity = capacity
        self._subscribers: set[asyncio.Queue[DeviceEvent]] = set()

    @property
    def subscriber_count(self) -> int:
        return len(self._subscribers)

    def publish(self, event: DeviceEvent) -> None:
        for queue in self._subscribers:
            try:
                queue.put_nowait(event)
            except asyncio.QueueFull:
                logger.warning("A subscriber is too slow; dropped %s for %s", event.kind, event.mac)

    async def subscribe(self) -> AsyncGenerator[DeviceEvent]:
        queue: asyncio.Queue[DeviceEvent] = asyncio.Queue(self._capacity)
        self._subscribers.add(queue)
        try:
            while True:
                yield await queue.get()
        finally:
            self._subscribers.discard(queue)
