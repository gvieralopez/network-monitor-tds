from network_monitor_tds.plugins.sdk.errors import PluginError


class TechnitiumError(PluginError):
    def __init__(self, status: str, message: str | None) -> None:
        super().__init__(f"Technitium answered {status!r}: {message or 'no details'}")
