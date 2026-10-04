from collections.abc import Mapping, Sequence
from datetime import datetime, timedelta, tzinfo

from network_monitor_tds.application.errors import DeviceNotFoundError
from network_monitor_tds.application.models import (
    DayPresence,
    DeviceDetail,
    DeviceSummary,
    HourState,
    NetworkOverview,
)
from network_monitor_tds.application.ports import UnitOfWork
from network_monitor_tds.domain.devices.identity import resolve_category, resolve_name
from network_monitor_tds.domain.devices.models import Device, DeviceLabels
from network_monitor_tds.domain.network.models import MacAddress
from network_monitor_tds.domain.observations.models import Fact, KnownField
from network_monitor_tds.domain.presence.models import Presence, PresenceInterval, PresenceState
from network_monitor_tds.domain.presence.timeline import HOUR, hourly_presence, uptime_ratio

DAY = timedelta(days=1)
HISTORY_DAYS = 14
UPTIME_DAYS = 7


async def list_devices(uow: UnitOfWork, now: datetime) -> list[DeviceSummary]:
    async with uow:
        devices = await uow.devices.list()
        facts = await uow.facts.all()
        presence = await uow.presence.all()
        intervals = await uow.presence.intervals_since(now - DAY)
    return [
        summarize(
            device,
            facts.get(device.mac, {}),
            presence.get(device.mac),
            intervals.get(device.mac, []),
            now,
        )
        for device in devices
    ]


def summarize(
    device: Device,
    facts: Mapping[str, Fact],
    presence: Presence | None,
    intervals: Sequence[PresenceInterval],
    now: datetime,
) -> DeviceSummary:
    vendor = facts.get(KnownField.VENDOR)
    return DeviceSummary(
        device=device,
        name=resolve_name(device.mac, device.labels, facts),
        category=resolve_category(device.labels, facts),
        vendor=vendor.value if vendor is not None else None,
        online=presence is not None and presence.state is PresenceState.ONLINE,
        last_24_hours=hourly_presence(intervals, _hour_start(now) - 23 * HOUR, 24, now),
    )


def network_overview(summaries: Sequence[DeviceSummary]) -> NetworkOverview:
    return NetworkOverview(
        total=len(summaries),
        online=sum(summary.online for summary in summaries),
        new=sum(summary.is_new for summary in summaries),
        seen_per_hour=tuple(
            sum(hours) for hours in zip(*(s.last_24_hours for s in summaries), strict=True)
        )
        or (0,) * 24,
    )


async def device_detail(
    uow: UnitOfWork, mac: MacAddress, now: datetime, timezone: tzinfo
) -> DeviceDetail:
    today = now.astimezone(timezone).replace(hour=0, minute=0, second=0, microsecond=0)
    async with uow:
        device = await _get(uow, mac)
        facts = await uow.facts.for_device(mac)
        detections = await uow.detections.for_device(mac)
        presence = await uow.presence.get(mac)
        intervals = (await uow.presence.intervals_since(today - HISTORY_DAYS * DAY)).get(mac, [])
    return DeviceDetail(
        summary=summarize(device, facts, presence, intervals, now),
        facts=facts,
        detections=tuple(detections.values()),
        days=tuple(
            _day_presence(intervals, today - offset * DAY, device.first_seen, now)
            for offset in range(HISTORY_DAYS)
        ),
        uptime_last_7_days=uptime_ratio(intervals, now - UPTIME_DAYS * DAY, now, now),
    )


async def describe_device(uow: UnitOfWork, mac: MacAddress) -> str:
    async with uow:
        device = await _get(uow, mac)
        facts = await uow.facts.for_device(mac)
    return resolve_name(mac, device.labels, facts).value


async def relabel_device(uow: UnitOfWork, mac: MacAddress, labels: DeviceLabels) -> Device:
    async with uow:
        device = (await _get(uow, mac)).relabel(labels)
        await uow.devices.save(device)
        await uow.commit()
    return device


async def acknowledge_device(uow: UnitOfWork, mac: MacAddress) -> Device:
    async with uow:
        device = (await _get(uow, mac)).acknowledge()
        await uow.devices.save(device)
        await uow.commit()
    return device


async def forget_device(uow: UnitOfWork, mac: MacAddress) -> str:
    async with uow:
        device = await _get(uow, mac)
        name = resolve_name(mac, device.labels, await uow.facts.for_device(mac)).value
        await uow.devices.delete(mac)
        await uow.commit()
    return name


def _hour_start(moment: datetime) -> datetime:
    return moment.replace(minute=0, second=0, microsecond=0)


async def _get(uow: UnitOfWork, mac: MacAddress) -> Device:
    device = await uow.devices.get(mac)
    if device is None:
        raise DeviceNotFoundError(mac)
    return device


def _day_presence(
    intervals: Sequence[PresenceInterval], start: datetime, first_seen: datetime, now: datetime
) -> DayPresence:
    online = hourly_presence(intervals, start, 24, now)
    return DayPresence(
        day=start.date(),
        hours=tuple(
            _hour_state(online[hour], start + hour * HOUR, first_seen, now) for hour in range(24)
        ),
    )


def _hour_state(online: bool, start: datetime, first_seen: datetime, now: datetime) -> HourState:
    if online:
        return HourState.ONLINE
    if start > now or start + HOUR <= first_seen:
        return HourState.UNKNOWN
    return HourState.OFFLINE
