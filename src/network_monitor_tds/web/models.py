from collections.abc import Callable, Mapping
from dataclasses import dataclass
from datetime import tzinfo

from network_monitor_tds.application.ports import EventSubscriber, PluginControl, UnitOfWork
from network_monitor_tds.domain.plugins.models import PluginId
from network_monitor_tds.domain.time import Clock
from network_monitor_tds.plugins.host.registry import PluginClass


@dataclass(frozen=True, slots=True)
class WebContext:
    unit_of_work: Callable[[], UnitOfWork]
    events: EventSubscriber
    clock: Clock
    plugins: Mapping[PluginId, PluginClass]
    control: PluginControl
    timezone: tzinfo

    @property
    def plugin_names(self) -> dict[PluginId, str]:
        return {plugin_id: plugin.info.name for plugin_id, plugin in self.plugins.items()}
