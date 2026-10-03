from datetime import timedelta

import pytest

from network_monitor_tds.domain.devices.models import Device
from network_monitor_tds.domain.events.models import DeviceEvent, EventKind
from tests.conftest import T0, Database

pytestmark = pytest.mark.anyio


async def test_recent_returns_newest_first_up_to_limit(
    database: Database, stored_device: Device
) -> None:
    events = [
        DeviceEvent(EventKind.DEVICE_DISCOVERED, stored_device.mac, T0),
        DeviceEvent(EventKind.DEVICE_ONLINE, stored_device.mac, T0),
        DeviceEvent(EventKind.DEVICE_OFFLINE, stored_device.mac, T0 + timedelta(hours=1)),
    ]
    async with database.unit_of_work() as uow:
        for event in events:
            await uow.events.add(event)
        await uow.commit()

    async with database.unit_of_work() as uow:
        assert await uow.events.recent(2) == [events[2], events[1]]
