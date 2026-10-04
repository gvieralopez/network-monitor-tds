from datetime import timedelta

import pytest

from network_monitor_tds.domain.devices.models import Device
from network_monitor_tds.domain.presence.models import Presence, PresenceInterval, PresenceState
from tests.conftest import T0, Database

pytestmark = pytest.mark.anyio

H = timedelta(hours=1)


async def test_presence_round_trip_and_update(database: Database, stored_device: Device) -> None:
    online = Presence(state=PresenceState.ONLINE, changed_at=T0, last_seen=T0)
    offline = Presence(state=PresenceState.OFFLINE, changed_at=T0 + H, last_seen=T0 + H)
    async with database.unit_of_work() as uow:
        assert await uow.presence.get(stored_device.mac) is None
        await uow.presence.save(stored_device.mac, online)
        await uow.presence.save(stored_device.mac, offline)
        await uow.commit()

    async with database.unit_of_work() as uow:
        assert await uow.presence.get(stored_device.mac) == offline
        assert await uow.presence.all() == {stored_device.mac: offline}


async def test_intervals_open_close_and_query(database: Database, stored_device: Device) -> None:
    async with database.unit_of_work() as uow:
        await uow.presence.open_interval(stored_device.mac, T0 - 30 * H)
        await uow.presence.close_interval(stored_device.mac, T0 - 26 * H)
        await uow.presence.open_interval(stored_device.mac, T0 - 2 * H)
        await uow.presence.close_interval(stored_device.mac, T0 - H)
        await uow.presence.open_interval(stored_device.mac, T0)
        await uow.commit()

    async with database.unit_of_work() as uow:
        intervals = await uow.presence.intervals_since(T0 - 24 * H)

    assert intervals == {
        stored_device.mac: [
            PresenceInterval(start=T0 - 2 * H, end=T0 - H),
            PresenceInterval(start=T0, end=None),
        ]
    }


async def test_close_interval_without_open_interval_is_a_no_op(
    database: Database, stored_device: Device
) -> None:
    async with database.unit_of_work() as uow:
        await uow.presence.close_interval(stored_device.mac, T0)
        assert await uow.presence.intervals_since(T0 - H) == {}


async def test_delete_intervals_ended_before_keeps_open_and_recent_ones(
    database: Database, stored_device: Device
) -> None:
    mac = stored_device.mac
    async with database.unit_of_work() as uow:
        await uow.presence.open_interval(mac, T0 - 30 * H)
        await uow.presence.close_interval(mac, T0 - 20 * H)
        await uow.presence.open_interval(mac, T0 - 10 * H)
        await uow.presence.close_interval(mac, T0 - 5 * H)
        await uow.presence.open_interval(mac, T0)
        await uow.commit()

    async with database.unit_of_work() as uow:
        assert await uow.presence.delete_intervals_ended_before(T0 - 5 * H) == 1
        await uow.commit()

    async with database.unit_of_work() as uow:
        intervals = (await uow.presence.intervals_since(T0 - 40 * H))[mac]
        assert [interval.start for interval in intervals] == [T0 - 10 * H, T0]
