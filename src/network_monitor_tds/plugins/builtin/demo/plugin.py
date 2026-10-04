from datetime import datetime, timedelta
from typing import ClassVar

from network_monitor_tds.domain.plugins.models import PluginId
from network_monitor_tds.plugins.builtin.demo.network import DEVICES
from network_monitor_tds.plugins.sdk.base import PluginContext, ScheduledPlugin
from network_monitor_tds.plugins.sdk.models import PluginInfo, PluginPurpose, ScheduledSettings


class DemoSettings(ScheduledSettings):
    interval: timedelta = timedelta(seconds=30)
    timeout: timedelta = timedelta(seconds=10)


class DemoPlugin(ScheduledPlugin[DemoSettings]):
    info = PluginInfo(
        plugin_id=PluginId("demo"),
        name="Demo network",
        description="Simulates a home network with daily routines, for development.",
        enabled_by_default=False,
        purpose=PluginPurpose.DEVELOPMENT,
    )
    settings_model: ClassVar[type[DemoSettings]] = DemoSettings

    def __init__(self, settings: DemoSettings) -> None:
        super().__init__(settings)
        self._started_at: datetime | None = None

    async def run(self, context: PluginContext) -> None:
        now = context.clock.now()
        self._started_at = self._started_at or now
        for device in DEVICES:
            if device.is_online(now, now - self._started_at):
                await context.sighting(device.mac, device.ip, device.fields)
