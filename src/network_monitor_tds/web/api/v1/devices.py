from fastapi import APIRouter

from network_monitor_tds.application.devices import list_devices
from network_monitor_tds.web.api.v1.schemas import DeviceOut
from network_monitor_tds.web.dependencies import ContextDep
from network_monitor_tds.web.models import WebContext

router = APIRouter(prefix="/api/v1/devices", tags=["devices"])


@router.get("")
async def all_devices(context: ContextDep) -> list[DeviceOut]:
    return await _devices(context)


@router.get("/online")
async def online_devices(context: ContextDep) -> list[DeviceOut]:
    return [device for device in await _devices(context) if device.online]


async def _devices(context: WebContext) -> list[DeviceOut]:
    summaries = await list_devices(context.unit_of_work(), context.clock.now())
    return [
        DeviceOut.from_summary(summary)
        for summary in sorted(summaries, key=lambda summary: summary.device.mac.value)
    ]
