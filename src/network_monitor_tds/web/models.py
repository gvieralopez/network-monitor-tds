from collections.abc import Callable, Mapping
from dataclasses import dataclass
from datetime import tzinfo

from network_monitor_tds.application.ports import EventSubscriber, UnitOfWork
from network_monitor_tds.domain.plugins.models import PluginId
from network_monitor_tds.domain.time import Clock
from network_monitor_tds.plugins.sdk.models import PluginInfo


@dataclass(frozen=True, slots=True)
class WebContext:
    unit_of_work: Callable[[], UnitOfWork]
    events: EventSubscriber
    clock: Clock
    plugins: Mapping[PluginId, PluginInfo]
    timezone: tzinfo
