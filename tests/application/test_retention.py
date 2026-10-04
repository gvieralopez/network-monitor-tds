from datetime import timedelta

import pytest

from network_monitor_tds.application.models import PruneResult
from network_monitor_tds.application.retention import prune_history
from network_monitor_tds.domain.devices.models import Device
from network_monitor_tds.domain.events.models import DeviceEvent, EventKind
from network_monitor_tds.domain.retention.models import RetentionPolicy
from tests.conftest import T0, Database

pytestmark = pytest.mark.anyio

DAY = timedelta(days=1)
NOW = T0 + 100 * DAY


async def test_prune_deletes_only_history_older_than_the_cutoff(
    database: Database, stored_device: Device
) -> None:
    mac = stored_device.mac
    async with database.unit_of_work() as uow:
        await uow.presence.open_interval(mac, T0)
        await uow.presence.close_interval(mac, T0 + DAY)
        await uow.presence.open_interval(mac, NOW - 20 * DAY)
        await uow.presence.close_interval(mac, NOW - 10 * DAY)
        await uow.presence.open_interval(mac, NOW - DAY)
        await uow.events.add(DeviceEvent(EventKind.DEVICE_DISCOVERED, mac, T0))
        await uow.events.add(DeviceEvent(EventKind.DEVICE_ONLINE, mac, NOW - DAY))
        await uow.commit()

    result = await prune_history(database.unit_of_work(), RetentionPolicy(14), NOW)

    assert result == PruneResult(intervals=1, events=1)
    async with database.unit_of_work() as uow:
        intervals = (await uow.presence.intervals_since(T0)).get(mac, [])
        assert [interval.start for interval in intervals] == [NOW - 20 * DAY, NOW - DAY]
        assert await uow.events.recent(10) == [DeviceEvent(EventKind.DEVICE_ONLINE, mac, NOW - DAY)]
        assert await uow.devices.get(mac) == stored_device
