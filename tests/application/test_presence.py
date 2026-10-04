from dataclasses import replace
from datetime import timedelta

import pytest

from network_monitor_tds.application.ingestion import ingest
from network_monitor_tds.application.presence import expire_presence
from network_monitor_tds.domain.events.models import DeviceEvent, EventKind
from network_monitor_tds.domain.network.models import MacAddress
from network_monitor_tds.domain.observations.models import KnownField, Observation
from network_monitor_tds.domain.presence.models import PresenceInterval, PresenceState
from network_monitor_tds.domain.presence.policy import DEFAULT_POLICY
from tests.conftest import T0, Database

pytestmark = pytest.mark.anyio

PHONE = MacAddress.parse("3a:f1:5c:22:9b:07")


async def test_expiry_respects_category_timeouts(
    database: Database, observation: Observation
) -> None:
    phone = replace(observation, mac=PHONE, fields={KnownField.DHCP_HOSTNAME: "Pixel-8"})
    await ingest(database.unit_of_work(), observation)
    await ingest(database.unit_of_work(), phone)

    events = await expire_presence(
        database.unit_of_work(), DEFAULT_POLICY, T0 + timedelta(minutes=12)
    )

    assert events == [DeviceEvent(EventKind.DEVICE_OFFLINE, observation.mac, T0)]
    async with database.unit_of_work() as uow:
        presence = await uow.presence.all()
        assert presence[observation.mac].state is PresenceState.OFFLINE
        assert presence[PHONE].state is PresenceState.ONLINE
        intervals = await uow.presence.intervals_since(T0)
        assert intervals[observation.mac] == [PresenceInterval(T0, T0)]


async def test_expiry_within_timeout_changes_nothing(
    database: Database, observation: Observation
) -> None:
    await ingest(database.unit_of_work(), observation)

    events = await expire_presence(
        database.unit_of_work(), DEFAULT_POLICY, T0 + timedelta(minutes=9)
    )

    assert events == []
