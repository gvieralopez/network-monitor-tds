import pytest

from network_monitor_tds.application.ports import UnitOfWork
from network_monitor_tds.domain.devices.models import Device
from network_monitor_tds.domain.network.models import MacAddress
from tests.conftest import T0, Database

pytestmark = pytest.mark.anyio


async def test_sql_unit_of_work_implements_port(database: Database, mac: MacAddress) -> None:
    uow: UnitOfWork = database.unit_of_work()
    async with uow:
        await uow.devices.save(Device.discovered(mac, None, T0))
        await uow.commit()

    async with database.unit_of_work() as check:
        assert await check.devices.get(mac) is not None


async def test_unit_of_work_rolls_back_on_error(database: Database, mac: MacAddress) -> None:
    with pytest.raises(RuntimeError):
        async with database.unit_of_work() as uow:
            await uow.devices.save(Device.discovered(mac, None, T0))
            raise RuntimeError

    async with database.unit_of_work() as uow:
        assert await uow.devices.get(mac) is None
