import asyncio
import logging
from datetime import timedelta
from typing import ClassVar

import pytest

from network_monitor_tds.application.errors import UnknownPluginError
from network_monitor_tds.application.models import PluginState
from network_monitor_tds.application.plugins import set_plugin_enabled, sync_plugin_configs
from network_monitor_tds.domain.devices.models import Device
from network_monitor_tds.domain.events.models import DeviceEvent, EventKind
from network_monitor_tds.domain.network.models import MacAddress
from network_monitor_tds.domain.plugins.models import PluginConfig, PluginId
from network_monitor_tds.infrastructure.messaging.bus import InMemoryEventBus
from network_monitor_tds.plugins.host.host import PluginHost, known_devices
from network_monitor_tds.plugins.host.registry import PluginClass, plugin_defaults
from network_monitor_tds.plugins.sdk.base import (
    EnrichmentPlugin,
    ListenerPlugin,
    PluginContext,
    ScheduledPlugin,
)
from network_monitor_tds.plugins.sdk.models import (
    KnownDevice,
    PluginInfo,
    PluginSettings,
    ScheduledSettings,
)
from tests.conftest import T0, Database, FixedClock, fast_sleep, no_known_devices, wait_until

pytestmark = pytest.mark.anyio

calls: dict[str, list[object]] = {}


def info(plugin_id: str, enabled: bool) -> PluginInfo:
    return PluginInfo(PluginId(plugin_id), plugin_id.title(), "Test plugin", enabled)


class EmptySettings(PluginSettings):
    pass


class TickSettings(ScheduledSettings):
    interval: timedelta = timedelta(seconds=1)
    timeout: timedelta = timedelta(seconds=1)
    label: str = "tick"


class CrashingListener(ListenerPlugin[EmptySettings]):
    info = info("listener", True)
    settings_model: ClassVar[type[EmptySettings]] = EmptySettings

    async def listen(self, context: PluginContext) -> None:
        calls["listener"].append(context.plugin_id)
        raise RuntimeError


class Ticker(ScheduledPlugin[TickSettings]):
    info = info("ticker", True)
    settings_model: ClassVar[type[TickSettings]] = TickSettings

    async def run(self, context: PluginContext) -> None:
        calls["ticker"].append(self.settings.label)


class Enricher(EnrichmentPlugin[EmptySettings]):
    info = info("enricher", True)
    settings_model: ClassVar[type[EmptySettings]] = EmptySettings

    async def enrich(self, context: PluginContext, mac: MacAddress) -> None:
        calls["enricher"].append(mac)


class Dormant(ScheduledPlugin[TickSettings]):
    info = info("dormant", False)
    settings_model: ClassVar[type[TickSettings]] = TickSettings

    async def run(self, context: PluginContext) -> None:
        calls["dormant"].append(1)


PLUGINS: dict[PluginId, PluginClass] = {
    plugin.info.plugin_id: plugin for plugin in (CrashingListener, Ticker, Enricher, Dormant)
}


@pytest.fixture(autouse=True)
def reset_calls() -> None:
    calls.clear()
    calls.update({plugin_id: [] for plugin_id in PLUGINS})


def host(database: Database, bus: InMemoryEventBus) -> PluginHost:
    return PluginHost(
        plugins=PLUGINS,
        unit_of_work=database.unit_of_work,
        events=bus,
        context_factory=lambda plugin_id: PluginContext(
            plugin_id,
            FixedClock(T0),
            _discard,
            logging.getLogger(f"tests.{plugin_id}"),
            no_known_devices,
        ),
        clock=FixedClock(T0),
        sleep=fast_sleep,
    )


async def test_runs_enabled_plugins_by_kind(database: Database, mac: MacAddress) -> None:
    bus = InMemoryEventBus(10)
    task = asyncio.create_task(host(database, bus).run())

    await wait_until(lambda: len(calls["listener"]) >= 2 and len(calls["ticker"]) >= 2)
    await wait_until(lambda: bus.subscriber_count == 1)
    bus.publish(DeviceEvent(EventKind.DEVICE_ONLINE, mac, T0))
    bus.publish(DeviceEvent(EventKind.DEVICE_DISCOVERED, mac, T0))
    await wait_until(lambda: calls["enricher"] == [mac])
    task.cancel()

    assert set(calls["ticker"]) == {"tick"}
    assert calls["dormant"] == []


async def test_enrichment_backfills_known_devices(
    database: Database, stored_device: Device
) -> None:
    task = asyncio.create_task(host(database, InMemoryEventBus(10)).run())

    await wait_until(lambda: calls["enricher"] == [stored_device.mac])
    task.cancel()


async def test_creates_default_configs(database: Database) -> None:
    task = asyncio.create_task(host(database, InMemoryEventBus(10)).run())
    await wait_until(lambda: len(calls["ticker"]) >= 1)
    task.cancel()

    async with database.unit_of_work() as uow:
        configs = {config.plugin_id: config.enabled for config in await uow.plugin_configs.list()}
    assert configs == {
        PluginId("listener"): True,
        PluginId("ticker"): True,
        PluginId("enricher"): True,
        PluginId("dormant"): False,
    }


async def test_uses_stored_settings_and_enabled_flags(database: Database) -> None:
    await sync_plugin_configs(database.unit_of_work(), plugin_defaults(PLUGINS), T0)
    await set_plugin_enabled(database.unit_of_work(), PluginId("dormant"), True, T0)
    await _store_ticker_settings(
        database, {"interval": "PT1S", "timeout": "PT1S", "label": "custom"}
    )

    task = asyncio.create_task(host(database, InMemoryEventBus(10)).run())
    await wait_until(lambda: len(calls["ticker"]) >= 1 and len(calls["dormant"]) >= 1)
    task.cancel()

    assert calls["ticker"][0] == "custom"


async def test_skips_plugins_with_invalid_settings(
    database: Database, caplog: pytest.LogCaptureFixture
) -> None:
    await sync_plugin_configs(database.unit_of_work(), plugin_defaults(PLUGINS), T0)
    await _store_ticker_settings(database, {"interval": "soon"})

    task = asyncio.create_task(host(database, InMemoryEventBus(10)).run())
    await wait_until(lambda: len(calls["listener"]) >= 1)
    task.cancel()

    assert calls["ticker"] == []
    assert "Plugin ticker has invalid settings" in caplog.text


async def _store_ticker_settings(database: Database, settings: dict[str, str]) -> None:
    async with database.unit_of_work() as uow:
        await uow.plugin_configs.save(PluginConfig(PluginId("ticker"), True, settings, T0))
        await uow.commit()


async def _discard(_observation: object) -> None:
    return None


async def test_reload_restarts_one_plugin_with_new_settings(database: Database) -> None:
    plugin_host = host(database, InMemoryEventBus(10))
    task = asyncio.create_task(plugin_host.run())
    await wait_until(lambda: len(calls["ticker"]) >= 1)

    await _store_ticker_settings(
        database, {"interval": "PT1S", "timeout": "PT1S", "label": "reloaded"}
    )
    await plugin_host.reload(PluginId("ticker"))
    await wait_until(lambda: "reloaded" in calls["ticker"])

    await set_plugin_enabled(database.unit_of_work(), PluginId("ticker"), False, T0)
    await plugin_host.reload(PluginId("ticker"))
    stopped_at = len(calls["ticker"])
    await asyncio.sleep(0.05)
    task.cancel()

    assert len(calls["ticker"]) == stopped_at
    assert plugin_host.status(PluginId("ticker")).state is PluginState.STOPPED
    assert plugin_host.status(PluginId("listener")).state is PluginState.FAILING


async def test_reload_unknown_plugin_fails(database: Database) -> None:
    with pytest.raises(UnknownPluginError):
        await host(database, InMemoryEventBus(10)).reload(PluginId("nope"))


async def test_reload_before_run_only_reads_config(database: Database) -> None:
    await sync_plugin_configs(database.unit_of_work(), plugin_defaults(PLUGINS), T0)
    plugin_host = host(database, InMemoryEventBus(10))

    await plugin_host.reload(PluginId("ticker"))

    assert plugin_host.status(PluginId("ticker")).state is PluginState.STOPPED


async def test_invalid_settings_are_reported_as_failing(database: Database) -> None:
    await sync_plugin_configs(database.unit_of_work(), plugin_defaults(PLUGINS), T0)
    await _store_ticker_settings(database, {"interval": "soon"})
    plugin_host = host(database, InMemoryEventBus(10))

    task = asyncio.create_task(plugin_host.run())
    await wait_until(lambda: len(calls["listener"]) >= 1)
    task.cancel()

    status = plugin_host.status(PluginId("ticker"))
    assert status.state is PluginState.FAILING
    assert status.last_error is not None
    assert status.last_error.startswith(
        "Invalid settings: interval: Input should be a valid timedelta"
    )


async def test_known_devices(database: Database, stored_device: Device) -> None:
    assert await known_devices(database.unit_of_work) == [
        KnownDevice(stored_device.mac, stored_device.ip, stored_device.last_seen)
    ]
