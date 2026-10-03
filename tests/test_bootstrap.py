import asyncio
from pathlib import Path

import pytest

from network_monitor_tds.application.plugins import set_plugin_enabled, sync_plugin_configs
from network_monitor_tds.bootstrap import build_container, prepare_database, serve
from network_monitor_tds.domain.plugins.models import PluginId
from network_monitor_tds.plugins.host.registry import plugin_defaults
from network_monitor_tds.settings import AppSettings
from tests.conftest import wait_until

pytestmark = pytest.mark.anyio


async def test_serve_monitors_the_demo_network(
    data_dir: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("NMTDS_PORT", "0")
    settings = AppSettings()
    container = build_container(settings)
    await prepare_database(container)
    await sync_plugin_configs(
        container.unit_of_work(), plugin_defaults(dict(container.plugins)), container.clock.now()
    )
    await set_plugin_enabled(
        container.unit_of_work(), PluginId("demo"), True, container.clock.now()
    )
    device_count = 0

    async def count_devices() -> None:
        nonlocal device_count
        async with container.unit_of_work() as uow:
            device_count = len(await uow.devices.list())

    server = asyncio.create_task(serve(settings))
    try:
        async with asyncio.timeout(10):
            while device_count == 0:
                await asyncio.sleep(0.05)
                await count_devices()
    finally:
        server.cancel()
        await container.engine.dispose()

    assert device_count > 0
    assert (data_dir / "nmtds.db").exists()
    await wait_until(server.done)
