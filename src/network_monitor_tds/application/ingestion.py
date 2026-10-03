from network_monitor_tds.application.ports import UnitOfWork
from network_monitor_tds.domain.devices.models import Device
from network_monitor_tds.domain.events.models import DeviceEvent, EventKind
from network_monitor_tds.domain.observations.detections import record_detection
from network_monitor_tds.domain.observations.facts import merge_facts
from network_monitor_tds.domain.observations.models import Observation, ObservationKind
from network_monitor_tds.domain.presence.tracker import record_sighting


async def ingest(uow: UnitOfWork, observation: Observation) -> list[DeviceEvent]:
    if observation.mac.is_multicast:
        return []
    async with uow:
        events = await _apply(uow, observation)
        await uow.commit()
    return events


async def _apply(uow: UnitOfWork, observation: Observation) -> list[DeviceEvent]:
    device = await uow.devices.get(observation.mac)
    is_sighting = observation.kind is ObservationKind.SIGHTING
    if device is None and not is_sighting:
        return []
    events = await _register_device(uow, device, observation)
    await _record_facts(uow, observation)
    if is_sighting:
        events += await _track_presence(uow, observation)
    for event in events:
        await uow.events.add(event)
    return events


async def _register_device(
    uow: UnitOfWork, device: Device | None, observation: Observation
) -> list[DeviceEvent]:
    mac, ip, at = observation.mac, observation.ip, observation.observed_at
    if device is None:
        await uow.devices.save(Device.discovered(mac, ip, at))
        return [DeviceEvent(EventKind.DEVICE_DISCOVERED, mac, at)]
    if observation.kind is ObservationKind.SIGHTING:
        await uow.devices.save(device.seen(ip, at))
    return []


async def _record_facts(uow: UnitOfWork, observation: Observation) -> None:
    mac, source = observation.mac, observation.source
    await uow.facts.save(mac, merge_facts(await uow.facts.for_device(mac), observation))
    detections = await uow.detections.for_device(mac)
    detection = record_detection(detections.get(source), source, observation.observed_at)
    await uow.detections.save(mac, detection)


async def _track_presence(uow: UnitOfWork, observation: Observation) -> list[DeviceEvent]:
    mac = observation.mac
    update = record_sighting(mac, await uow.presence.get(mac), observation.observed_at)
    await uow.presence.save(mac, update.presence)
    if update.event is None:
        return []
    await uow.presence.open_interval(mac, update.event.occurred_at)
    return [update.event]
