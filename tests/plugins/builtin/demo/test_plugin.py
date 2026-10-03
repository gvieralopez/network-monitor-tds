import logging
from datetime import datetime, timedelta

import pytest

from network_monitor_tds.domain.observations.models import Observation
from network_monitor_tds.plugins.builtin.demo.network import DEVICES
from network_monitor_tds.plugins.builtin.demo.plugin import DemoPlugin, DemoSettings
from network_monitor_tds.plugins.sdk.base import PluginContext

pytestmark = pytest.mark.anyio

LOCAL = datetime.now().astimezone().tzinfo
SATURDAY_NIGHT = datetime(2026, 10, 3, 22, tzinfo=LOCAL)


class SteppingClock:
    def __init__(self, start: datetime) -> None:
        self.at = start

    def now(self) -> datetime:
        return self.at


async def test_delayed_devices_join_after_start() -> None:
    seen: list[Observation] = []
    clock = SteppingClock(SATURDAY_NIGHT)

    async def collect(observation: Observation) -> None:
        seen.append(observation)

    plugin = DemoPlugin(DemoSettings())
    context = PluginContext(DemoPlugin.info.plugin_id, clock, collect, logging.getLogger("demo"))

    await plugin.run(context)
    first_run = {observation.mac for observation in seen}
    clock.at += timedelta(minutes=10)
    seen.clear()
    await plugin.run(context)
    second_run = {observation.mac for observation in seen}

    delayed = {device.mac for device in DEVICES if device.appears_after}
    assert first_run.isdisjoint(delayed)
    assert delayed <= second_run
    assert all(observation.source == "demo" for observation in seen)
