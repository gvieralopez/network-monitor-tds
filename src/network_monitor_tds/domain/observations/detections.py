from dataclasses import replace
from datetime import datetime

from network_monitor_tds.domain.observations.models import Detection
from network_monitor_tds.domain.plugins.models import PluginId


def record_detection(current: Detection | None, source: PluginId, at: datetime) -> Detection:
    if current is None:
        return Detection(source=source, first_seen=at, last_seen=at)
    return replace(
        current, first_seen=min(current.first_seen, at), last_seen=max(current.last_seen, at)
    )
