from datetime import timedelta

import pytest

from network_monitor_tds.domain.plugins.models import PluginConfig, PluginId
from tests.conftest import T0, Database

pytestmark = pytest.mark.anyio

TECHNITIUM = PluginConfig(
    plugin_id=PluginId("technitium"),
    enabled=True,
    settings={"url": "http://192.168.1.10:5380", "interval_seconds": 300, "tags": ["a", "b"]},
    updated_at=T0,
)
NMAP = PluginConfig(plugin_id=PluginId("nmap"), enabled=False, settings={}, updated_at=T0)


async def test_save_get_and_list(database: Database) -> None:
    async with database.unit_of_work() as uow:
        assert await uow.plugin_configs.get(TECHNITIUM.plugin_id) is None
        await uow.plugin_configs.save(TECHNITIUM)
        await uow.plugin_configs.save(NMAP)
        await uow.commit()

    async with database.unit_of_work() as uow:
        assert await uow.plugin_configs.get(TECHNITIUM.plugin_id) == TECHNITIUM
        assert await uow.plugin_configs.list() == [NMAP, TECHNITIUM]


async def test_save_updates_config(database: Database) -> None:
    disabled = PluginConfig(
        plugin_id=TECHNITIUM.plugin_id,
        enabled=False,
        settings={"url": "http://technitium:5380"},
        updated_at=T0 + timedelta(minutes=1),
    )
    async with database.unit_of_work() as uow:
        await uow.plugin_configs.save(TECHNITIUM)
        await uow.plugin_configs.save(disabled)
        await uow.commit()

    async with database.unit_of_work() as uow:
        assert await uow.plugin_configs.get(TECHNITIUM.plugin_id) == disabled
