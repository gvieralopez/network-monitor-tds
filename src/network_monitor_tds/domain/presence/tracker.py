from dataclasses import replace
from datetime import datetime, timedelta

from network_monitor_tds.domain.events.models import DeviceEvent, EventKind
from network_monitor_tds.domain.network.models import MacAddress
from network_monitor_tds.domain.presence.models import Presence, PresenceState, PresenceUpdate


def record_sighting(mac: MacAddress, presence: Presence | None, at: datetime) -> PresenceUpdate:
    if presence is None or _comes_back_online(presence, at):
        online = Presence(state=PresenceState.ONLINE, changed_at=at, last_seen=at)
        return PresenceUpdate(online, DeviceEvent(EventKind.DEVICE_ONLINE, mac, at))
    return PresenceUpdate(replace(presence, last_seen=max(presence.last_seen, at)), None)


def expire(
    mac: MacAddress, presence: Presence, now: datetime, timeout: timedelta
) -> PresenceUpdate:
    if presence.state is PresenceState.ONLINE and now - presence.last_seen > timeout:
        offline = Presence(
            state=PresenceState.OFFLINE, changed_at=presence.last_seen, last_seen=presence.last_seen
        )
        return PresenceUpdate(
            offline, DeviceEvent(EventKind.DEVICE_OFFLINE, mac, presence.last_seen)
        )
    return PresenceUpdate(presence, None)


def _comes_back_online(presence: Presence, at: datetime) -> bool:
    return presence.state is PresenceState.OFFLINE and at > presence.changed_at
