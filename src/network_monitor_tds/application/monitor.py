import asyncio
import logging
from collections.abc import Callable
from datetime import timedelta

from network_monitor_tds.application.ingestion import ingest
from network_monitor_tds.application.ports import EventPublisher, UnitOfWork
from network_monitor_tds.application.preferences import load_presence_policy
from network_monitor_tds.application.presence import expire_presence
from network_monitor_tds.application.scheduling import SILENT, Sleep, run_periodically
from network_monitor_tds.domain.observations.models import Observation
from network_monitor_tds.domain.time import Clock

logger = logging.getLogger(__name__)

PRESENCE_CHECK_INTERVAL = timedelta(minutes=1)
PRESENCE_CHECK_TIMEOUT = timedelta(seconds=30)


class Monitor:
    def __init__(
        self,
        unit_of_work: Callable[[], UnitOfWork],
        publisher: EventPublisher,
        clock: Clock,
        queue_size: int,
    ) -> None:
        self._unit_of_work = unit_of_work
        self._publisher = publisher
        self._clock = clock
        self._queue: asyncio.Queue[Observation] = asyncio.Queue(queue_size)

    async def emit(self, observation: Observation) -> None:
        await self._queue.put(observation)

    async def run_ingestion(self) -> None:
        while True:
            observation = await self._queue.get()
            try:
                await self._ingest(observation)
            finally:
                self._queue.task_done()

    async def run_presence_checks(self, sleep: Sleep) -> None:
        await run_periodically(
            self._check_presence,
            PRESENCE_CHECK_INTERVAL,
            PRESENCE_CHECK_TIMEOUT,
            sleep,
            logger,
            SILENT,
        )

    async def drain(self) -> None:
        await self._queue.join()

    async def _ingest(self, observation: Observation) -> None:
        try:
            events = await ingest(self._unit_of_work(), observation)
        except Exception:
            logger.exception("Could not ingest an observation from %s", observation.source)
            return
        for event in events:
            self._publisher.publish(event)

    async def _check_presence(self) -> None:
        policy = await load_presence_policy(self._unit_of_work())
        events = await expire_presence(self._unit_of_work(), policy, self._clock.now())
        for event in events:
            self._publisher.publish(event)
