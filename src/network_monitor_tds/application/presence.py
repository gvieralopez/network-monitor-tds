from datetime import datetime

from network_monitor_tds.application.ports import UnitOfWork
from network_monitor_tds.domain.devices.identity import resolve_category
from network_monitor_tds.domain.events.models import DeviceEvent
from network_monitor_tds.domain.presence.policy import PresencePolicy
from network_monitor_tds.domain.presence.tracker import expire


async def expire_presence(
    uow: UnitOfWork, policy: PresencePolicy, now: datetime
) -> list[DeviceEvent]:
    async with uow:
        devices = {device.mac: device for device in await uow.devices.list()}
        facts = await uow.facts.all()
        events: list[DeviceEvent] = []
        for mac, presence in (await uow.presence.all()).items():
            category = resolve_category(devices[mac].labels, facts.get(mac, {})).value
            update = expire(mac, presence, now, policy.timeout_for(category))
            if update.event is not None:
                await uow.presence.save(mac, update.presence)
                await uow.presence.close_interval(mac, update.event.occurred_at)
                await uow.events.add(update.event)
                events.append(update.event)
        await uow.commit()
    return events
