import asyncio
import logging
from collections.abc import Callable, Mapping
from datetime import timedelta
from functools import partial
from typing import Any

from pydantic import ValidationError

from network_monitor_tds.application.errors import UnknownPluginError
from network_monitor_tds.application.models import Backoff, PluginStatus
from network_monitor_tds.application.plugins import get_plugin_config, sync_plugin_configs
from network_monitor_tds.application.ports import EventSubscriber, UnitOfWork
from network_monitor_tds.application.scheduling import (
    Reporter,
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
from network_monitor_tds.plugins.host.status import StatusBoard
from network_monitor_tds.plugins.sdk.base import (
    EnrichmentPlugin,
    ListenerPlugin,
    Plugin,
    PluginContext,
    ScheduledPlugin,
)
from network_monitor_tds.plugins.sdk.models import KnownDevice

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
        self._statuses = StatusBoard(clock)
        self._tasks: dict[PluginId, asyncio.Task[None]] = {}
        self._group: asyncio.TaskGroup | None = None

    async def run(self) -> None:
        configs = await sync_plugin_configs(
            self._unit_of_work(), plugin_defaults(dict(self._plugins)), self._clock.now()
        )
        async with asyncio.TaskGroup() as group:
            self._group = group
            for config in configs.values():
                self._start(config)
            await asyncio.Event().wait()

    async def reload(self, plugin_id: PluginId) -> None:
        if plugin_id not in self._plugins:
            raise UnknownPluginError(plugin_id)
        config = await get_plugin_config(self._unit_of_work(), plugin_id)
        await self._stop(plugin_id)
        self._start(config)

    def status(self, plugin_id: PluginId) -> PluginStatus:
        return self._statuses.get(plugin_id)

    def _start(self, config: PluginConfig) -> None:
        if self._group is None or not config.enabled:
            return
        plugin = self._instantiate(config)
        if plugin is None:
            return
        logger.info("Starting plugin %s", config.plugin_id)
        self._statuses.running(config.plugin_id)
        self._tasks[config.plugin_id] = self._group.create_task(
            self._run(plugin), name=f"plugin:{config.plugin_id}"
        )

    async def _stop(self, plugin_id: PluginId) -> None:
        task = self._tasks.pop(plugin_id, None)
        if task is None:
            return
        logger.info("Stopping plugin %s", plugin_id)
        task.cancel()
        await asyncio.wait([task])
        self._statuses.stopped(plugin_id)

    def _instantiate(self, config: PluginConfig) -> Plugin[Any] | None:
        plugin_class = self._plugins[config.plugin_id]
        try:
            settings = plugin_class.settings_model.model_validate(config.settings)
        except ValidationError as error:
            logger.exception("Plugin %s has invalid settings; not starting it", config.plugin_id)
            self._statuses.failed(config.plugin_id, f"Invalid settings: {_first_problem(error)}")
            return None
        return plugin_class(settings)

    async def _run(self, plugin: Plugin[Any]) -> None:
        context = self._context_factory(plugin.info.plugin_id)
        reporter = self._statuses.reporter(plugin.info.plugin_id)
        match plugin:
            case ListenerPlugin():
                await run_with_restarts(
                    lambda: plugin.listen(context),
                    LISTENER_BACKOFF,
                    self._sleep,
                    context.logger,
                    reporter,
                )
            case ScheduledPlugin():
                await run_periodically(
                    lambda: plugin.run(context),
                    plugin.settings.interval,
                    plugin.settings.timeout,
                    self._sleep,
                    context.logger,
                    reporter,
                )
            case EnrichmentPlugin():
                await self._run_enrichment(plugin, context, reporter)

    async def _run_enrichment(
        self, plugin: EnrichmentPlugin[Any], context: PluginContext, reporter: Reporter
    ) -> None:
        async with self._events.subscribe() as events:
            for mac in await self._known_devices():
                await _enrich(plugin, context, reporter, mac)
            async for event in events:
                if event.kind is EventKind.DEVICE_DISCOVERED:
                    await _enrich(plugin, context, reporter, event.mac)

    async def _known_devices(self) -> list[MacAddress]:
        return [device.mac for device in await known_devices(self._unit_of_work)]


async def known_devices(unit_of_work: Callable[[], UnitOfWork]) -> list[KnownDevice]:
    async with unit_of_work() as uow:
        return [
            KnownDevice(device.mac, device.ip, device.last_seen)
            for device in await uow.devices.list()
        ]


def _first_problem(error: ValidationError) -> str:
    detail = error.errors()[0]
    location = ".".join(str(part) for part in detail["loc"])
    return f"{location}: {detail['msg']}" if location else detail["msg"]


async def _enrich(
    plugin: EnrichmentPlugin[Any], context: PluginContext, reporter: Reporter, mac: MacAddress
) -> None:
    job = partial(plugin.enrich, context, mac)
    await run_once(job, ENRICHMENT_TIMEOUT, context.logger, reporter)
