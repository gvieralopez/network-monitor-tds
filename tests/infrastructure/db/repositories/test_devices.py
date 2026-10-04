from datetime import timedelta
from ipaddress import IPv4Address

import pytest

from network_monitor_tds.domain.devices.models import Category, Device, DeviceLabels
from network_monitor_tds.domain.network.models import MacAddress
from tests.conftest import T0, Database

pytestmark = pytest.mark.anyio


async def test_get_returns_none_for_unknown_device(database: Database, mac: MacAddress) -> None:
    async with database.unit_of_work() as uow:
        assert await uow.devices.get(mac) is None


async def test_save_and_get_round_trip(database: Database, stored_device: Device) -> None:
    async with database.unit_of_work() as uow:
        assert await uow.devices.get(stored_device.mac) == stored_device


async def test_save_updates_existing_device(database: Database, stored_device: Device) -> None:
    labels = DeviceLabels(name="Espressif sensor", category=Category.IOT, icon="chip")
    updated = stored_device.seen(IPv4Address("192.168.1.200"), T0 + timedelta(hours=1)).relabel(
        labels
    )

    async with database.unit_of_work() as uow:
        await uow.devices.save(updated)
        await uow.commit()
    async with database.unit_of_work() as uow:
        assert await uow.devices.get(stored_device.mac) == updated


async def test_list_orders_by_mac(database: Database, stored_device: Device) -> None:
    other = Device.discovered(MacAddress.parse("00:11:32:c4:7e:92"), None, T0)
    async with database.unit_of_work() as uow:
        await uow.devices.save(other)
        await uow.commit()

    async with database.unit_of_work() as uow:
        assert await uow.devices.list() == [other, stored_device]


async def test_changes_are_discarded_without_commit(database: Database, mac: MacAddress) -> None:
    async with database.unit_of_work() as uow:
        await uow.devices.save(Device.discovered(mac, None, T0))

    async with database.unit_of_work() as uow:
        assert await uow.devices.get(mac) is None
