from datetime import timedelta

import pytest

from network_monitor_tds.domain.devices.models import Device
from network_monitor_tds.domain.observations.models import Fact, KnownField
from tests.conftest import ARP_SWEEP, DHCP_SNIFF, T0, Database

pytestmark = pytest.mark.anyio

HOSTNAME = Fact(name=KnownField.DHCP_HOSTNAME, value="esp-31f5e", source=DHCP_SNIFF, observed_at=T0)
VENDOR = Fact(name=KnownField.VENDOR, value="Espressif", source=ARP_SWEEP, observed_at=T0)


async def test_save_and_load_facts(database: Database, stored_device: Device) -> None:
    async with database.unit_of_work() as uow:
        await uow.facts.save(stored_device.mac, {HOSTNAME.name: HOSTNAME, VENDOR.name: VENDOR})
        await uow.commit()

    async with database.unit_of_work() as uow:
        assert await uow.facts.for_device(stored_device.mac) == {
            HOSTNAME.name: HOSTNAME,
            VENDOR.name: VENDOR,
        }
        assert await uow.facts.all() == {
            stored_device.mac: {HOSTNAME.name: HOSTNAME, VENDOR.name: VENDOR}
        }


async def test_save_overwrites_fact(database: Database, stored_device: Device) -> None:
    renamed = Fact(
        name=HOSTNAME.name, value="sensor", source=DHCP_SNIFF, observed_at=T0 + timedelta(hours=1)
    )
    async with database.unit_of_work() as uow:
        await uow.facts.save(stored_device.mac, {HOSTNAME.name: HOSTNAME})
        await uow.facts.save(stored_device.mac, {HOSTNAME.name: renamed})
        await uow.commit()

    async with database.unit_of_work() as uow:
        assert await uow.facts.for_device(stored_device.mac) == {HOSTNAME.name: renamed}
