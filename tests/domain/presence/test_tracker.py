from datetime import timedelta

import pytest

from network_monitor_tds.domain.events.models import DeviceEvent, EventKind
from network_monitor_tds.domain.network.models import MacAddress
from network_monitor_tds.domain.presence.models import Presence, PresenceState
from network_monitor_tds.domain.presence.tracker import expire, record_sighting
from tests.conftest import T0

TIMEOUT = timedelta(minutes=10)
ONLINE = Presence(state=PresenceState.ONLINE, changed_at=T0, last_seen=T0)
OFFLINE = Presence(state=PresenceState.OFFLINE, changed_at=T0, last_seen=T0)


def test_first_sighting_goes_online(mac: MacAddress) -> None:
    update = record_sighting(mac, None, T0)

    assert update.presence == ONLINE
    assert update.event == DeviceEvent(EventKind.DEVICE_ONLINE, mac, T0)


def test_sighting_while_online_extends_last_seen(mac: MacAddress) -> None:
    later = T0 + timedelta(minutes=3)

    update = record_sighting(mac, ONLINE, later)

    assert update.presence == Presence(state=PresenceState.ONLINE, changed_at=T0, last_seen=later)
    assert update.event is None


def test_out_of_order_sighting_keeps_latest(mac: MacAddress) -> None:
    update = record_sighting(mac, ONLINE, T0 - timedelta(minutes=3))

    assert update.presence == ONLINE
    assert update.event is None


def test_sighting_after_offline_comes_back(mac: MacAddress) -> None:
    later = T0 + timedelta(hours=2)

    update = record_sighting(mac, OFFLINE, later)

    assert update.presence == Presence(
        state=PresenceState.ONLINE, changed_at=later, last_seen=later
    )
    assert update.event == DeviceEvent(EventKind.DEVICE_ONLINE, mac, later)


@pytest.mark.parametrize("offset", [timedelta(), timedelta(minutes=-1)])
def test_stale_sighting_does_not_revive_offline_device(mac: MacAddress, offset: timedelta) -> None:
    update = record_sighting(mac, OFFLINE, T0 + offset)

    assert update.presence == OFFLINE
    assert update.event is None


@pytest.mark.parametrize("elapsed", [timedelta(minutes=1), TIMEOUT])
def test_expire_keeps_device_online_within_timeout(mac: MacAddress, elapsed: timedelta) -> None:
    update = expire(mac, ONLINE, T0 + elapsed, TIMEOUT)

    assert update.presence is ONLINE
    assert update.event is None


def test_expire_marks_offline_at_last_seen(mac: MacAddress) -> None:
    update = expire(mac, ONLINE, T0 + TIMEOUT + timedelta(seconds=1), TIMEOUT)

    assert update.presence == OFFLINE
    assert update.event == DeviceEvent(EventKind.DEVICE_OFFLINE, mac, T0)


def test_expire_ignores_offline_device(mac: MacAddress) -> None:
    update = expire(mac, OFFLINE, T0 + timedelta(days=1), TIMEOUT)

    assert update.presence is OFFLINE
    assert update.event is None
