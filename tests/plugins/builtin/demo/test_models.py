from datetime import datetime, timedelta
from ipaddress import IPv4Address

import pytest

from network_monitor_tds.domain.network.models import MacAddress
from network_monitor_tds.plugins.builtin.demo.models import DemoDevice, Routine

LOCAL = datetime.now().astimezone().tzinfo
WEDNESDAY_NOON = datetime(2026, 9, 30, 12, tzinfo=LOCAL)
WEDNESDAY_NIGHT = datetime(2026, 9, 30, 21, tzinfo=LOCAL)
SATURDAY_NOON = datetime(2026, 10, 3, 12, tzinfo=LOCAL)
RUNNING = timedelta(hours=1)


def device(routine: Routine, appears_after: timedelta) -> DemoDevice:
    return DemoDevice(
        MacAddress.parse("02:00:00:00:00:01"), IPv4Address("10.0.0.1"), routine, appears_after, {}
    )


@pytest.mark.parametrize(
    ("routine", "now", "online"),
    [
        (Routine.ALWAYS, WEDNESDAY_NIGHT, True),
        (Routine.WORKDAY, WEDNESDAY_NOON, True),
        (Routine.WORKDAY, WEDNESDAY_NIGHT, False),
        (Routine.WORKDAY, SATURDAY_NOON, False),
        (Routine.EVENING, WEDNESDAY_NIGHT, True),
        (Routine.EVENING, WEDNESDAY_NOON, False),
        (Routine.PHONE, WEDNESDAY_NOON, False),
        (Routine.PHONE, WEDNESDAY_NIGHT, True),
        (Routine.PHONE, SATURDAY_NOON, True),
    ],
)
def test_routines(routine: Routine, now: datetime, online: bool) -> None:
    assert device(routine, timedelta()).is_online(now, RUNNING) is online


def test_sporadic_is_online_some_hours() -> None:
    hours = [WEDNESDAY_NOON + timedelta(hours=offset) for offset in range(24)]
    sporadic = device(Routine.SPORADIC, timedelta())

    online = [hour for hour in hours if sporadic.is_online(hour, RUNNING)]

    assert len(online) == 6


def test_delayed_devices_appear_later() -> None:
    delayed = device(Routine.ALWAYS, timedelta(minutes=5))

    assert delayed.is_online(WEDNESDAY_NOON, timedelta(minutes=4)) is False
    assert delayed.is_online(WEDNESDAY_NOON, timedelta(minutes=5)) is True
