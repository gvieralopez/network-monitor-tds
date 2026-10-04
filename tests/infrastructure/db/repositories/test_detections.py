from datetime import timedelta

import pytest

from network_monitor_tds.domain.devices.models import Device
from network_monitor_tds.domain.observations.models import Detection
from tests.conftest import ARP_SWEEP, DHCP_SNIFF, T0, Database

pytestmark = pytest.mark.anyio


async def test_detections_are_keyed_by_source_in_discovery_order(
    database: Database, stored_device: Device
) -> None:
    first = Detection(source=DHCP_SNIFF, first_seen=T0, last_seen=T0 + timedelta(minutes=5))
    later = Detection(source=ARP_SWEEP, first_seen=T0 + timedelta(minutes=1), last_seen=T0)
    async with database.unit_of_work() as uow:
        await uow.detections.save(stored_device.mac, later)
        await uow.detections.save(stored_device.mac, first)
        await uow.commit()

    async with database.unit_of_work() as uow:
        detections = await uow.detections.for_device(stored_device.mac)

    assert list(detections) == [DHCP_SNIFF, ARP_SWEEP]
    assert detections[DHCP_SNIFF] == first


async def test_save_updates_detection(database: Database, stored_device: Device) -> None:
    detection = Detection(source=ARP_SWEEP, first_seen=T0, last_seen=T0)
    updated = Detection(source=ARP_SWEEP, first_seen=T0, last_seen=T0 + timedelta(hours=2))
    async with database.unit_of_work() as uow:
        await uow.detections.save(stored_device.mac, detection)
        await uow.detections.save(stored_device.mac, updated)
        await uow.commit()

    async with database.unit_of_work() as uow:
        assert await uow.detections.for_device(stored_device.mac) == {ARP_SWEEP: updated}
