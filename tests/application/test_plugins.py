from datetime import timedelta

import pytest

from network_monitor_tds.application.errors import UnknownPluginError
from network_monitor_tds.application.plugins import (
    get_plugin_config,
    list_plugin_configs,
    set_plugin_enabled,
    sync_plugin_configs,
    update_plugin_settings,
)
from network_monitor_tds.domain.plugins.models import PluginConfig, PluginDefaults, PluginId
from tests.conftest import T0, Database

pytestmark = pytest.mark.anyio

DEMO = PluginId("demo")
OUI = PluginId("oui")
DEFAULTS = {
    DEMO: PluginDefaults(enabled=False, settings={"interval": "PT30S"}),
    OUI: PluginDefaults(enabled=True, settings={}),
}


async def test_sync_creates_missing_configs_from_defaults(database: Database) -> None:
    configs = await sync_plugin_configs(database.unit_of_work(), DEFAULTS, T0)

    assert configs == {
        DEMO: PluginConfig(DEMO, enabled=False, settings={"interval": "PT30S"}, updated_at=T0),
        OUI: PluginConfig(OUI, enabled=True, settings={}, updated_at=T0),
    }
    assert list(await list_plugin_configs(database.unit_of_work())) == list(configs.values())


async def test_sync_keeps_existing_configs_and_skips_uninstalled(database: Database) -> None:
    await sync_plugin_configs(database.unit_of_work(), DEFAULTS, T0)
    await set_plugin_enabled(database.unit_of_work(), DEMO, True, T0 + timedelta(hours=1))

    configs = await sync_plugin_configs(
        database.unit_of_work(), {DEMO: DEFAULTS[DEMO]}, T0 + timedelta(hours=2)
    )

    assert list(configs) == [DEMO]
    assert configs[DEMO].enabled is True
    assert configs[DEMO].updated_at == T0 + timedelta(hours=1)


async def test_set_enabled_for_unknown_plugin_fails(database: Database) -> None:
    with pytest.raises(UnknownPluginError, match="nope"):
        await set_plugin_enabled(database.unit_of_work(), PluginId("nope"), True, T0)


async def test_update_plugin_settings(database: Database) -> None:
    await sync_plugin_configs(database.unit_of_work(), DEFAULTS, T0)
    later = T0 + timedelta(minutes=1)

    updated = await update_plugin_settings(
        database.unit_of_work(), DEMO, {"interval": "PT1M"}, later
    )

    assert updated == await get_plugin_config(database.unit_of_work(), DEMO)
    assert (updated.settings, updated.updated_at) == ({"interval": "PT1M"}, later)


async def test_settings_for_unknown_plugin_fail(database: Database) -> None:
    with pytest.raises(UnknownPluginError):
        await get_plugin_config(database.unit_of_work(), PluginId("nope"))
    with pytest.raises(UnknownPluginError):
        await update_plugin_settings(database.unit_of_work(), PluginId("nope"), {}, T0)
