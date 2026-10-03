from dataclasses import replace
from datetime import UTC, timedelta

import pytest

from network_monitor_tds.application.devices import (
    acknowledge_device,
    describe_device,
    device_detail,
    list_devices,
    network_overview,
    relabel_device,
)
from network_monitor_tds.application.errors import DeviceNotFoundError
from network_monitor_tds.application.ingestion import ingest
from network_monitor_tds.application.models import HourState
from network_monitor_tds.domain.devices.models import Category, DeviceLabels
from network_monitor_tds.domain.network.models import MacAddress
from network_monitor_tds.domain.observations.models import KnownField, Observation
from tests.conftest import ARP_SWEEP, DHCP_SNIFF, T0, Database

pytestmark = pytest.mark.anyio

NOW = T0 + timedelta(minutes=30)
UNKNOWN = MacAddress.parse("aa:bb:cc:dd:ee:ff")


async def test_list_devices_summarizes_identity_and_presence(
    database: Database, observation: Observation
) -> None:
    await ingest(
        database.unit_of_work(),
        replace(
            observation,
            fields={KnownField.DHCP_HOSTNAME: "esp-31f5e", KnownField.VENDOR: "Espressif Inc."},
        ),
    )

    [summary] = await list_devices(database.unit_of_work(), NOW)

    assert summary.name.value == "esp-31f5e"
    assert summary.category.value is Category.IOT
    assert summary.vendor == "Espressif Inc."
    assert summary.online is True
    assert summary.is_new is True
    assert summary.last_24_hours == (False,) * 23 + (True,)
    assert summary.hours_online == 1


async def test_network_overview(database: Database, observation: Observation) -> None:
    await ingest(database.unit_of_work(), observation)
    await ingest(database.unit_of_work(), replace(observation, mac=UNKNOWN))
    await acknowledge_device(database.unit_of_work(), UNKNOWN)

    overview = network_overview(await list_devices(database.unit_of_work(), NOW))

    assert (overview.total, overview.online, overview.new) == (2, 2, 1)
    assert overview.seen_per_hour[-1] == 2
    assert len(overview.seen_per_hour) == 24


def test_network_overview_of_empty_network() -> None:
    overview = network_overview([])

    assert (overview.total, overview.online, overview.new) == (0, 0, 0)
    assert overview.seen_per_hour == (0,) * 24


async def test_device_detail(database: Database, observation: Observation) -> None:
    await ingest(database.unit_of_work(), observation)
    await ingest(
        database.unit_of_work(),
        replace(observation, source=ARP_SWEEP, observed_at=T0 + timedelta(minutes=10), fields={}),
    )

    detail = await device_detail(database.unit_of_work(), observation.mac, NOW, UTC)

    assert [detection.source for detection in detail.detections] == [DHCP_SNIFF, ARP_SWEEP]
    assert len(detail.days) == 14
    today = detail.days[0]
    assert today.day == NOW.date()
    assert today.hours[11] is HourState.UNKNOWN
    assert today.hours[12] is HourState.ONLINE
    assert today.hours[13] is HourState.UNKNOWN
    assert set(detail.days[1].hours) == {HourState.UNKNOWN}
    assert 0 < detail.uptime_last_7_days < 0.01


async def test_device_detail_marks_offline_hours_after_first_seen(
    database: Database, observation: Observation
) -> None:
    await ingest(database.unit_of_work(), observation)
    async with database.unit_of_work() as uow:
        await uow.presence.close_interval(observation.mac, T0)
        await uow.commit()

    detail = await device_detail(
        database.unit_of_work(), observation.mac, T0 + timedelta(hours=3), UTC
    )

    assert detail.days[0].hours[12:16] == (
        HourState.ONLINE,
        HourState.OFFLINE,
        HourState.OFFLINE,
        HourState.OFFLINE,
    )


async def test_describe_relabel_and_acknowledge(
    database: Database, observation: Observation
) -> None:
    await ingest(database.unit_of_work(), observation)
    labels = DeviceLabels(name="Garden sensor", category=Category.IOT, icon="bulb")

    assert await describe_device(database.unit_of_work(), observation.mac) == "esp-31f5e"
    relabelled = await relabel_device(database.unit_of_work(), observation.mac, labels)
    assert relabelled.labels == labels
    assert await describe_device(database.unit_of_work(), observation.mac) == "Garden sensor"
    assert (await acknowledge_device(database.unit_of_work(), observation.mac)).acknowledged


async def test_unknown_device(database: Database) -> None:
    no_labels = DeviceLabels(None, None, None)

    with pytest.raises(DeviceNotFoundError, match="aa:bb:cc:dd:ee:ff"):
        await describe_device(database.unit_of_work(), UNKNOWN)
    with pytest.raises(DeviceNotFoundError):
        await device_detail(database.unit_of_work(), UNKNOWN, NOW, UTC)
    with pytest.raises(DeviceNotFoundError):
        await relabel_device(database.unit_of_work(), UNKNOWN, no_labels)
    with pytest.raises(DeviceNotFoundError):
        await acknowledge_device(database.unit_of_work(), UNKNOWN)
