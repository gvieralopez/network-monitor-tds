import asyncio

import pytest

from network_monitor_tds.domain.events.models import DeviceEvent, EventKind
from network_monitor_tds.domain.network.models import MacAddress
from network_monitor_tds.infrastructure.messaging.bus import InMemoryEventBus
from tests.conftest import T0, wait_until

pytestmark = pytest.mark.anyio


def event(mac: MacAddress, kind: EventKind) -> DeviceEvent:
    return DeviceEvent(kind, mac, T0)


async def test_every_subscriber_receives_published_events(mac: MacAddress) -> None:
    bus = InMemoryEventBus(10)
    first, second = bus.subscribe(), bus.subscribe()
    pending = [asyncio.ensure_future(anext(first)), asyncio.ensure_future(anext(second))]
    await wait_until(lambda: bus.subscriber_count == 2)

    bus.publish(event(mac, EventKind.DEVICE_ONLINE))

    assert await asyncio.gather(*pending) == [event(mac, EventKind.DEVICE_ONLINE)] * 2
    await first.aclose()
    await second.aclose()
    assert bus.subscriber_count == 0


async def test_slow_subscriber_drops_events(
    mac: MacAddress, caplog: pytest.LogCaptureFixture
) -> None:
    bus = InMemoryEventBus(1)
    subscription = bus.subscribe()
    pending = asyncio.ensure_future(anext(subscription))
    await wait_until(lambda: bus.subscriber_count == 1)

    bus.publish(event(mac, EventKind.DEVICE_ONLINE))
    bus.publish(event(mac, EventKind.DEVICE_OFFLINE))

    async with asyncio.timeout(5):
        assert await pending == event(mac, EventKind.DEVICE_ONLINE)
    assert "dropped device_offline" in caplog.text
    await subscription.aclose()


def test_publish_without_subscribers_is_a_no_op(mac: MacAddress) -> None:
    InMemoryEventBus(1).publish(event(mac, EventKind.DEVICE_ONLINE))
