from dataclasses import replace

from network_monitor_tds.application.models import STOPPED, PluginState, PluginStatus
from network_monitor_tds.domain.plugins.models import PluginId
from network_monitor_tds.domain.time import Clock


class StatusBoard:
    def __init__(self, clock: Clock) -> None:
        self._clock = clock
        self._statuses: dict[PluginId, PluginStatus] = {}

    def get(self, plugin_id: PluginId) -> PluginStatus:
        return self._statuses.get(plugin_id, STOPPED)

    def reporter(self, plugin_id: PluginId) -> PluginReporter:
        return PluginReporter(self, plugin_id)

    def stopped(self, plugin_id: PluginId) -> None:
        self._statuses[plugin_id] = replace(self.get(plugin_id), state=PluginState.STOPPED)

    def running(self, plugin_id: PluginId) -> None:
        self._statuses[plugin_id] = replace(self.get(plugin_id), state=PluginState.RUNNING)

    def succeeded(self, plugin_id: PluginId) -> None:
        self._statuses[plugin_id] = PluginStatus(
            state=PluginState.RUNNING, last_success=self._clock.now(), last_error=None
        )

    def failed(self, plugin_id: PluginId, reason: str) -> None:
        self._statuses[plugin_id] = replace(
            self.get(plugin_id), state=PluginState.FAILING, last_error=reason
        )


class PluginReporter:
    def __init__(self, board: StatusBoard, plugin_id: PluginId) -> None:
        self._board = board
        self._plugin_id = plugin_id

    def running(self) -> None:
        self._board.running(self._plugin_id)

    def succeeded(self) -> None:
        self._board.succeeded(self._plugin_id)

    def failed(self, reason: str) -> None:
        self._board.failed(self._plugin_id, reason)
