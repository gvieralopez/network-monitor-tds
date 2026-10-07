import asyncio
import json

import pytest

from network_monitor_tds.domain.events.models import DeviceEvent, EventKind
from network_monitor_tds.domain.network.models import MacAddress
from network_monitor_tds.infrastructure.messaging.bus import InMemoryEventBus
from network_monitor_tds.web.models import WebContext
from network_monitor_tds.web.sse import CONNECTED, device_events
from tests.conftest import T0

pytestmark = pytest.mark.anyio


async def test_streams_device_events_with_names(
    web_context: WebContext, seen_device: MacAddress
) -> None:
    bus = web_context.events
    assert isinstance(bus, InMemoryEventBus)
    stream = device_events(web_context)
    assert await anext(stream) == CONNECTED
    assert bus.subscriber_count == 1
    pending = asyncio.ensure_future(anext(stream))

    bus.publish(DeviceEvent(EventKind.DEVICE_OFFLINE, MacAddress.parse("aa:bb:cc:dd:ee:ff"), T0))
    bus.publish(DeviceEvent(EventKind.DEVICE_ONLINE, seen_device, T0))

    async with asyncio.timeout(5):
        message = await pending
    assert message.event == "device"
    assert json.loads(str(message.data)) == {
        "kind": "device_online",
        "mac": str(seen_device),
        "name": "esp-31f5e",
    }
