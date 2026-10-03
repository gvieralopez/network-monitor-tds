from ipaddress import IPv4Network

from network_monitor_tds.plugins.sdk.errors import PluginError


class CapturePermissionError(PluginError, PermissionError):
    def __init__(self) -> None:
        super().__init__(
            "Capturing packets needs the CAP_NET_RAW and CAP_NET_ADMIN capabilities "
            "(run as root, or grant them to the Python interpreter or container)"
        )


class UnknownNetworkError(PluginError):
    def __init__(self, interface: str) -> None:
        super().__init__(
            f"Could not find the IPv4 subnet of interface {interface!r}; set it in the settings"
        )


class NetworkTooLargeError(PluginError):
    def __init__(self, network: IPv4Network, limit: int) -> None:
        super().__init__(
            f"Refusing to sweep {network} ({network.num_addresses} addresses); the limit is {limit}"
        )
