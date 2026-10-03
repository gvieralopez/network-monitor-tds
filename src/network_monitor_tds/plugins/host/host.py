import asyncio
import logging
from collections.abc import Callable, Mapping
from datetime import timedelta
from functools import partial
from typing import Any

from pydantic import ValidationError

from network_monitor_tds.application.models import Backoff
from network_monitor_tds.application.plugins import sync_plugin_configs
from network_monitor_tds.application.ports import EventSubscriber, UnitOfWork
from network_monitor_tds.application.scheduling import (
    Sleep,
    run_once,
    run_periodically,
    run_with_restarts,
)
from network_monitor_tds.domain.events.models import EventKind
from network_monitor_tds.domain.network.models import MacAddress
from network_monitor_tds.domain.plugins.models import PluginConfig, PluginId
from network_monitor_tds.domain.time import Clock
from network_monitor_tds.plugins.host.registry import PluginClass, plugin_defaults
from network_monitor_tds.plugins.sdk.base import (
    EnrichmentPlugin,
    ListenerPlugin,
    Plugin,
    PluginContext,
    ScheduledPlugin,
)

logger = logging.getLogger(__name__)

LISTENER_BACKOFF = Backoff(initial=timedelta(seconds=1), maximum=timedelta(minutes=5))
ENRICHMENT_TIMEOUT = timedelta(seconds=30)

type ContextFactory = Callable[[PluginId], PluginContext]


class PluginHost:
    def __init__(
        self,
        plugins: Mapping[PluginId, PluginClass],
        unit_of_work: Callable[[], UnitOfWork],
        events: EventSubscriber,
        context_factory: ContextFactory,
        clock: Clock,
        sleep: Sleep,
    ) -> None:
        self._plugins = plugins
        self._unit_of_work = unit_of_work
        self._events = events
        self._context_factory = context_factory
        self._clock = clock
        self._sleep = sleep

    async def run(self) -> None:
        configs = await sync_plugin_configs(
            self._unit_of_work(), plugin_defaults(dict(self._plugins)), self._clock.now()
        )
        async with asyncio.TaskGroup() as group:
            for plugin_id, config in configs.items():
                plugin = self._instantiate(config) if config.enabled else None
                if plugin is not None:
                    logger.info("Starting plugin %s", plugin_id)
                    group.create_task(self._run(plugin), name=f"plugin:{plugin_id}")

    def _instantiate(self, config: PluginConfig) -> Plugin[Any] | None:
        plugin_class = self._plugins[config.plugin_id]
        try:
            settings = plugin_class.settings_model.model_validate(config.settings)
        except ValidationError:
            logger.exception("Plugin %s has invalid settings; not starting it", config.plugin_id)
            return None
        return plugin_class(settings)

    async def _run(self, plugin: Plugin[Any]) -> None:
        context = self._context_factory(plugin.info.plugin_id)
        match plugin:
            case ListenerPlugin():
                await run_with_restarts(
                    lambda: plugin.listen(context), LISTENER_BACKOFF, self._sleep, context.logger
                )
            case ScheduledPlugin():
                await run_periodically(
                    lambda: plugin.run(context),
                    plugin.settings.interval,
                    plugin.settings.timeout,
                    self._sleep,
                    context.logger,
                )
            case EnrichmentPlugin():
                await self._run_enrichment(plugin, context)

    async def _run_enrichment(self, plugin: EnrichmentPlugin[Any], context: PluginContext) -> None:
        async with self._events.subscribe() as events:
            for mac in await self._known_devices():
                await _enrich(plugin, context, mac)
            async for event in events:
                if event.kind is EventKind.DEVICE_DISCOVERED:
                    await _enrich(plugin, context, event.mac)

    async def _known_devices(self) -> list[MacAddress]:
        async with self._unit_of_work() as uow:
            return [device.mac for device in await uow.devices.list()]


async def _enrich(plugin: EnrichmentPlugin[Any], context: PluginContext, mac: MacAddress) -> None:
    await run_once(partial(plugin.enrich, context, mac), ENRICHMENT_TIMEOUT, context.logger)
