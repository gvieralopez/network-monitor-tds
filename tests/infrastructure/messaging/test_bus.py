import asyncio

import pytest

from network_monitor_tds.domain.events.models import DeviceEvent, EventKind
from network_monitor_tds.domain.network.models import MacAddress
from network_monitor_tds.infrastructure.messaging.bus import InMemoryEventBus
from tests.conftest import T0

pytestmark = pytest.mark.anyio


def event(mac: MacAddress, kind: EventKind) -> DeviceEvent:
    return DeviceEvent(kind, mac, T0)


async def test_subscribers_receive_events_published_after_subscribing(mac: MacAddress) -> None:
    bus = InMemoryEventBus(10)

    async with bus.subscribe() as first, bus.subscribe() as second:
        assert bus.subscriber_count == 2
        bus.publish(event(mac, EventKind.DEVICE_ONLINE))
        async with asyncio.timeout(5):
            received = [await anext(first), await anext(second)]

    assert received == [event(mac, EventKind.DEVICE_ONLINE)] * 2
    assert bus.subscriber_count == 0


async def test_slow_subscriber_drops_events(
    mac: MacAddress, caplog: pytest.LogCaptureFixture
) -> None:
    bus = InMemoryEventBus(1)

    async with bus.subscribe() as events:
        bus.publish(event(mac, EventKind.DEVICE_ONLINE))
        bus.publish(event(mac, EventKind.DEVICE_OFFLINE))
        async with asyncio.timeout(5):
            assert await anext(events) == event(mac, EventKind.DEVICE_ONLINE)

    assert "dropped device_offline" in caplog.text


def test_publish_without_subscribers_is_a_no_op(mac: MacAddress) -> None:
    InMemoryEventBus(1).publish(event(mac, EventKind.DEVICE_ONLINE))
