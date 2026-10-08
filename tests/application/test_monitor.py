import asyncio
import logging
from datetime import timedelta

import pytest

from network_monitor_tds.application.monitor import Monitor
from network_monitor_tds.application.ports import UnitOfWork
from network_monitor_tds.domain.devices.models import Device
from network_monitor_tds.domain.events.models import DeviceEvent, EventKind
from network_monitor_tds.domain.observations.models import Observation
from tests.conftest import T0, Database, FixedClock, Stop, stop

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
    monitor = Monitor(database.unit_of_work, publisher, FixedClock(T0), 10)

    await _ingest(monitor, observation)

    assert [event.kind for event in publisher.events] == [
        EventKind.DEVICE_DISCOVERED,
        EventKind.DEVICE_ONLINE,
    ]


async def test_failed_ingestion_is_logged_and_skipped(
    observation: Observation, caplog: pytest.LogCaptureFixture
) -> None:
    publisher = RecordingPublisher()
    monitor = Monitor(_broken_unit_of_work, publisher, FixedClock(T0), 10)

    await _ingest(monitor, observation)

    assert "Could not ingest an observation from dhcp-sniff" in caplog.text
    assert publisher.events == []


async def test_presence_checks_publish_offline_events(
    database: Database, observation: Observation
) -> None:
    publisher = RecordingPublisher()
    online = Monitor(database.unit_of_work, publisher, FixedClock(T0), 10)
    await _ingest(online, observation)
    an_hour_later = FixedClock(T0 + timedelta(hours=1))
    later = Monitor(database.unit_of_work, publisher, an_hour_later, 10)

    with pytest.raises(Stop):
        await later.run_presence_checks(_stop)

    assert publisher.events[-1] == DeviceEvent(EventKind.DEVICE_OFFLINE, observation.mac, T0)


async def test_pruning_deletes_old_history(
    database: Database, stored_device: Device, caplog: pytest.LogCaptureFixture
) -> None:
    async with database.unit_of_work() as uow:
        await uow.events.add(DeviceEvent(EventKind.DEVICE_DISCOVERED, stored_device.mac, T0))
        await uow.commit()
    a_year_later = FixedClock(T0 + timedelta(days=365))
    monitor = Monitor(database.unit_of_work, RecordingPublisher(), a_year_later, 10)

    with caplog.at_level(logging.INFO), pytest.raises(Stop):
        await monitor.run_pruning(_stop)

    assert "Pruned 0 presence intervals and 1 events older than 90 days" in caplog.text
    async with database.unit_of_work() as uow:
        assert await uow.events.recent(10) == []


async def _ingest(monitor: Monitor, observation: Observation) -> None:
    worker = asyncio.create_task(monitor.run_ingestion())
    await monitor.emit(observation)
    await monitor.drain()
    await stop(worker)


def _broken_unit_of_work() -> UnitOfWork:
    raise RuntimeError


async def _stop(_seconds: float) -> None:
    raise Stop
