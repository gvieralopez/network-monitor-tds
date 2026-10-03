from network_monitor_tds.domain.network.models import MacAddress
from network_monitor_tds.domain.plugins.models import PluginId
from network_monitor_tds.errors import NetworkMonitorError


class ApplicationError(NetworkMonitorError):
    pass


class UnknownPluginError(ApplicationError, LookupError):
    def __init__(self, plugin_id: PluginId) -> None:
        super().__init__(f"No plugin is installed with id {plugin_id!r}")


class DeviceNotFoundError(ApplicationError, LookupError):
    def __init__(self, mac: MacAddress) -> None:
        super().__init__(f"No device with MAC address {mac}")
