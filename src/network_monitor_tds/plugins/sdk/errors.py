from network_monitor_tds.domain.plugins.models import PluginId
from network_monitor_tds.errors import NetworkMonitorError


class PluginError(NetworkMonitorError):
    pass


class DuplicatePluginError(PluginError):
    def __init__(self, plugin_id: PluginId) -> None:
        super().__init__(f"More than one installed plugin uses the id {plugin_id!r}")
