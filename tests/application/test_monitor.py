import asyncio
from datetime import timedelta

import pytest

from network_monitor_tds.application.monitor import Monitor
from network_monitor_tds.application.ports import UnitOfWork
from network_monitor_tds.domain.events.models import DeviceEvent, EventKind
from network_monitor_tds.domain.observations.models import Observation
from network_monitor_tds.domain.presence.policy import DEFAULT_POLICY
from tests.conftest import T0, Database, FixedClock, Stop

pytestmark = pytest.mark.anyio


class RecordingPublisher:
    def __init__(self) -> None:
        self.events: list[DeviceEvent] = []

    def publish(self, event: DeviceEvent) -> None:
        self.events.append(event)


async def test_ingests_queued_observations_and_publishes_events(
    database: Database, observation: Observation
) -> None:
    publisher = RecordingPublisher()
    monitor = Monitor(database.unit_of_work, publisher, FixedClock(T0), DEFAULT_POLICY, 10)

    await _ingest(monitor, observation)

    assert [event.kind for event in publisher.events] == [
        EventKind.DEVICE_DISCOVERED,
        EventKind.DEVICE_ONLINE,
    ]


async def test_failed_ingestion_is_logged_and_skipped(
    observation: Observation, caplog: pytest.LogCaptureFixture
) -> None:
    publisher = RecordingPublisher()
    monitor = Monitor(_broken_unit_of_work, publisher, FixedClock(T0), DEFAULT_POLICY, 10)

    await _ingest(monitor, observation)

    assert "Could not ingest an observation from dhcp-sniff" in caplog.text
    assert publisher.events == []


async def test_presence_checks_publish_offline_events(
    database: Database, observation: Observation
) -> None:
    publisher = RecordingPublisher()
    online = Monitor(database.unit_of_work, publisher, FixedClock(T0), DEFAULT_POLICY, 10)
    await _ingest(online, observation)
    an_hour_later = FixedClock(T0 + timedelta(hours=1))
    later = Monitor(database.unit_of_work, publisher, an_hour_later, DEFAULT_POLICY, 10)

    with pytest.raises(Stop):
        await later.run_presence_checks(_stop)

    assert publisher.events[-1] == DeviceEvent(EventKind.DEVICE_OFFLINE, observation.mac, T0)


async def _ingest(monitor: Monitor, observation: Observation) -> None:
    worker = asyncio.create_task(monitor.run_ingestion())
    await monitor.emit(observation)
    await monitor.drain()
    worker.cancel()


def _broken_unit_of_work() -> UnitOfWork:
    raise RuntimeError


async def _stop(_seconds: float) -> None:
    raise Stop
