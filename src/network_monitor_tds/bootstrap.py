import asyncio
import logging
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from datetime import UTC, datetime, tzinfo
from functools import partial

import uvicorn
from fastapi import FastAPI
from sqlalchemy.ext.asyncio import AsyncEngine

from network_monitor_tds.application.monitor import Monitor
from network_monitor_tds.application.ports import UnitOfWork
from network_monitor_tds.domain.plugins.models import PluginId
from network_monitor_tds.infrastructure.clock import SystemClock
from network_monitor_tds.infrastructure.db.engine import create_engine, create_session_factory
from network_monitor_tds.infrastructure.db.migrator import upgrade_to_head
from network_monitor_tds.infrastructure.db.unit_of_work import unit_of_work_factory
from network_monitor_tds.infrastructure.messaging.bus import InMemoryEventBus
from network_monitor_tds.plugins.host.host import PluginHost, known_devices
from network_monitor_tds.plugins.host.registry import PluginClass, discover_plugins
from network_monitor_tds.plugins.sdk.base import PluginContext
from network_monitor_tds.settings import AppSettings
from network_monitor_tds.web.app import create_app
from network_monitor_tds.web.models import WebContext

logger = logging.getLogger(__name__)

SHUTDOWN_GRACE_SECONDS = 2


@dataclass(frozen=True, slots=True)
class Container:
    settings: AppSettings
    engine: AsyncEngine
    unit_of_work: Callable[[], UnitOfWork]
    clock: SystemClock
    bus: InMemoryEventBus
    monitor: Monitor
    plugins: Mapping[PluginId, PluginClass]
    host: PluginHost


async def serve(settings: AppSettings) -> None:
    container = build_container(settings)
    try:
        await prepare_database(container)
        logger.info("Installed plugins: %s", ", ".join(container.plugins) or "none")
        async with asyncio.TaskGroup() as group:
            group.create_task(container.monitor.run_ingestion(), name="ingestion")
            group.create_task(container.monitor.run_presence_checks(asyncio.sleep), name="presence")
            group.create_task(container.monitor.run_pruning(asyncio.sleep), name="pruning")
            group.create_task(container.host.run(), name="plugins")
            group.create_task(_web_server(container).serve(), name="web")
    finally:
        await container.engine.dispose()


def build_container(settings: AppSettings) -> Container:
    engine = create_engine(settings.database_path)
    unit_of_work = unit_of_work_factory(create_session_factory(engine))
    clock = SystemClock()
    bus = InMemoryEventBus(settings.event_queue_size)
    monitor = Monitor(unit_of_work, bus, clock, settings.observation_queue_size)
    plugins = discover_plugins()
    host = PluginHost(
        plugins=plugins,
        unit_of_work=unit_of_work,
        events=bus,
        context_factory=lambda plugin_id: PluginContext(
            plugin_id=plugin_id,
            clock=clock,
            emit=monitor.emit,
            logger=logging.getLogger(f"network_monitor_tds.plugins.{plugin_id}"),
            known_devices=partial(known_devices, unit_of_work),
        ),
        clock=clock,
        sleep=asyncio.sleep,
    )
    return Container(
        settings=settings,
        engine=engine,
        unit_of_work=unit_of_work,
        clock=clock,
        bus=bus,
        monitor=monitor,
        plugins=plugins,
        host=host,
    )


async def prepare_database(container: Container) -> None:
    container.settings.data_dir.mkdir(parents=True, exist_ok=True)
    await upgrade_to_head(container.engine, container.settings.database_path)


def create_web_app(container: Container) -> FastAPI:
    return create_app(
        WebContext(
            unit_of_work=container.unit_of_work,
            events=container.bus,
            clock=container.clock,
            plugins=container.plugins,
            control=container.host,
            timezone=_local_timezone(),
        )
    )


def _web_server(container: Container) -> uvicorn.Server:
    settings = container.settings
    logger.info("Web interface on http://%s:%s", settings.host, settings.port)
    config = uvicorn.Config(
        create_web_app(container),
        host=settings.host,
        port=settings.port,
        lifespan="off",
        log_level="warning",
        timeout_graceful_shutdown=SHUTDOWN_GRACE_SECONDS,
    )
    return uvicorn.Server(config)


def _local_timezone() -> tzinfo:
    return datetime.now().astimezone().tzinfo or UTC
