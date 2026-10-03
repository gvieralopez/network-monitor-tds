import json
from collections.abc import AsyncIterator

from fastapi import APIRouter
from sse_starlette import EventSourceResponse, ServerSentEvent

from network_monitor_tds.application.devices import describe_device
from network_monitor_tds.application.errors import DeviceNotFoundError
from network_monitor_tds.web.dependencies import ContextDep
from network_monitor_tds.web.models import WebContext

PING_SECONDS = 15

router = APIRouter()


@router.get("/events")
async def events(context: ContextDep) -> EventSourceResponse:
    return EventSourceResponse(device_events(context), ping=PING_SECONDS)


async def device_events(context: WebContext) -> AsyncIterator[ServerSentEvent]:
    async for event in context.events.subscribe():
        try:
            name = await describe_device(context.unit_of_work(), event.mac)
        except DeviceNotFoundError:
            continue
        payload = {"kind": event.kind, "mac": str(event.mac), "name": name}
        yield ServerSentEvent(data=json.dumps(payload, indent=2), event="device")
