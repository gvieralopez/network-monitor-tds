from datetime import datetime

from network_monitor_tds.domain.devices.models import Category, Device, DeviceLabels
from network_monitor_tds.domain.events.models import DeviceEvent, EventKind
from network_monitor_tds.domain.network.models import MacAddress
from network_monitor_tds.domain.observations.models import Detection, Fact
from network_monitor_tds.domain.plugins.models import PluginConfig, PluginId
from network_monitor_tds.domain.presence.models import Presence, PresenceInterval, PresenceState
from network_monitor_tds.infrastructure.db.models import (
    DetectionRecord,
    DeviceRecord,
    EventRecord,
    FactRecord,
    PluginConfigRecord,
    PresenceIntervalRecord,
    PresenceRecord,
)


def device_from_record(record: DeviceRecord) -> Device:
    return Device(
        mac=record.mac,
        ip=record.ip,
        first_seen=record.first_seen,
        last_seen=record.last_seen,
        acknowledged=record.acknowledged,
        labels=DeviceLabels(
            name=record.label_name,
            category=Category(record.label_category) if record.label_category else None,
            icon=record.label_icon,
        ),
    )


def write_device(record: DeviceRecord, device: Device) -> DeviceRecord:
    record.mac = device.mac
    record.ip = device.ip
    record.first_seen = device.first_seen
    record.last_seen = device.last_seen
    record.acknowledged = device.acknowledged
    record.label_name = device.labels.name
    record.label_category = device.labels.category
    record.label_icon = device.labels.icon
    return record


def fact_from_record(record: FactRecord) -> Fact:
    return Fact(
        name=record.name,
        value=record.value,
        source=PluginId(record.source),
        observed_at=record.observed_at,
    )


def write_fact(record: FactRecord, mac: MacAddress, fact: Fact) -> FactRecord:
    record.mac = mac
    record.name = fact.name
    record.value = fact.value
    record.source = fact.source
    record.observed_at = fact.observed_at
    return record


def detection_from_record(record: DetectionRecord) -> Detection:
    return Detection(
        source=PluginId(record.source), first_seen=record.first_seen, last_seen=record.last_seen
    )


def write_detection(
    record: DetectionRecord, mac: MacAddress, detection: Detection
) -> DetectionRecord:
    record.mac = mac
    record.source = detection.source
    record.first_seen = detection.first_seen
    record.last_seen = detection.last_seen
    return record


def presence_from_record(record: PresenceRecord) -> Presence:
    return Presence(
        state=PresenceState(record.state), changed_at=record.changed_at, last_seen=record.last_seen
    )


def write_presence(record: PresenceRecord, mac: MacAddress, presence: Presence) -> PresenceRecord:
    record.mac = mac
    record.state = presence.state
    record.changed_at = presence.changed_at
    record.last_seen = presence.last_seen
    return record


def interval_from_record(record: PresenceIntervalRecord) -> PresenceInterval:
    return PresenceInterval(start=record.started_at, end=record.ended_at)


def interval_record(mac: MacAddress, start: datetime) -> PresenceIntervalRecord:
    return PresenceIntervalRecord(mac=mac, started_at=start, ended_at=None)


def event_from_record(record: EventRecord) -> DeviceEvent:
    return DeviceEvent(kind=EventKind(record.kind), mac=record.mac, occurred_at=record.occurred_at)


def event_record(event: DeviceEvent) -> EventRecord:
    return EventRecord(kind=event.kind, mac=event.mac, occurred_at=event.occurred_at)


def plugin_config_from_record(record: PluginConfigRecord) -> PluginConfig:
    return PluginConfig(
        plugin_id=PluginId(record.plugin_id),
        enabled=record.enabled,
        settings=record.settings,
        updated_at=record.updated_at,
    )


def write_plugin_config(record: PluginConfigRecord, config: PluginConfig) -> PluginConfigRecord:
    record.plugin_id = config.plugin_id
    record.enabled = config.enabled
    record.settings = dict(config.settings)
    record.updated_at = config.updated_at
    return record
