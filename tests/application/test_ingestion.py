from dataclasses import replace
from datetime import timedelta
from ipaddress import IPv4Address

import pytest

from network_monitor_tds.application.ingestion import ingest
from network_monitor_tds.domain.events.models import DeviceEvent, EventKind
from network_monitor_tds.domain.network.models import MacAddress
from network_monitor_tds.domain.observations.models import (
    Detection,
    KnownField,
    Observation,
    ObservationKind,
)
from network_monitor_tds.domain.presence.models import Presence, PresenceInterval, PresenceState
from tests.conftest import DHCP_SNIFF, T0, Database

pytestmark = pytest.mark.anyio

LATER = T0 + timedelta(minutes=5)


async def test_first_sighting_registers_device(
    database: Database, observation: Observation
) -> None:
    events = await ingest(database.unit_of_work(), observation)

    mac = observation.mac
    assert events == [
        DeviceEvent(EventKind.DEVICE_DISCOVERED, mac, T0),
        DeviceEvent(EventKind.DEVICE_ONLINE, mac, T0),
    ]
    async with database.unit_of_work() as uow:
        device = await uow.devices.get(mac)
        assert device is not None
        assert device.ip == observation.ip
        assert device.acknowledged is False
        assert (await uow.facts.for_device(mac))[KnownField.DHCP_HOSTNAME].value == "esp-31f5e"
        assert await uow.detections.for_device(mac) == {DHCP_SNIFF: Detection(DHCP_SNIFF, T0, T0)}
        assert await uow.presence.get(mac) == Presence(PresenceState.ONLINE, T0, T0)
        assert await uow.presence.intervals_since(T0) == {mac: [PresenceInterval(T0, None)]}
        assert await uow.events.recent(10) == list(reversed(events))


async def test_repeated_sighting_updates_without_events(
    database: Database, observation: Observation
) -> None:
    await ingest(database.unit_of_work(), observation)
    new_ip = IPv4Address("192.168.1.200")

    events = await ingest(
        database.unit_of_work(), replace(observation, ip=new_ip, observed_at=LATER)
    )

    assert events == []
    async with database.unit_of_work() as uow:
        device = await uow.devices.get(observation.mac)
        assert device is not None
        assert (device.ip, device.last_seen) == (new_ip, LATER)
        assert await uow.presence.get(observation.mac) == Presence(PresenceState.ONLINE, T0, LATER)
        detection = (await uow.detections.for_device(observation.mac))[DHCP_SNIFF]
        assert detection == Detection(DHCP_SNIFF, T0, LATER)


async def test_enrichment_for_unknown_device_is_ignored(
    database: Database, observation: Observation
) -> None:
    enrichment = replace(observation, kind=ObservationKind.ENRICHMENT)

    assert await ingest(database.unit_of_work(), enrichment) == []
    async with database.unit_of_work() as uow:
        assert await uow.devices.get(observation.mac) is None


async def test_enrichment_adds_facts_without_touching_presence(
    database: Database, observation: Observation
) -> None:
    await ingest(database.unit_of_work(), observation)
    enrichment = replace(
        observation,
        kind=ObservationKind.ENRICHMENT,
        ip=None,
        observed_at=LATER,
        fields={KnownField.VENDOR: "Espressif"},
    )

    events = await ingest(database.unit_of_work(), enrichment)

    assert events == []
    async with database.unit_of_work() as uow:
        device = await uow.devices.get(observation.mac)
        assert device is not None
        assert device.last_seen == T0
        assert (await uow.facts.for_device(observation.mac))[KnownField.VENDOR].value == "Espressif"
        assert await uow.presence.get(observation.mac) == Presence(PresenceState.ONLINE, T0, T0)


async def test_multicast_sources_are_ignored(database: Database, observation: Observation) -> None:
    multicast = replace(observation, mac=MacAddress.parse("01:00:5e:00:00:fb"))

    assert await ingest(database.unit_of_work(), multicast) == []
    async with database.unit_of_work() as uow:
        assert await uow.devices.list() == []


async def test_sighting_after_offline_reopens_interval(
    database: Database, observation: Observation
) -> None:
    await ingest(database.unit_of_work(), observation)
    async with database.unit_of_work() as uow:
        await uow.presence.save(observation.mac, Presence(PresenceState.OFFLINE, T0, T0))
        await uow.presence.close_interval(observation.mac, T0)
        await uow.commit()

    events = await ingest(database.unit_of_work(), replace(observation, observed_at=LATER))

    assert events == [DeviceEvent(EventKind.DEVICE_ONLINE, observation.mac, LATER)]
    async with database.unit_of_work() as uow:
        assert await uow.presence.intervals_since(T0) == {
            observation.mac: [PresenceInterval(T0, T0), PresenceInterval(LATER, None)]
        }
