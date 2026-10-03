from collections.abc import Mapping, Sequence
from dataclasses import replace
from datetime import datetime

from network_monitor_tds.application.errors import UnknownPluginError
from network_monitor_tds.application.ports import UnitOfWork
from network_monitor_tds.domain.plugins.models import PluginConfig, PluginDefaults, PluginId


async def sync_plugin_configs(
    uow: UnitOfWork, defaults: Mapping[PluginId, PluginDefaults], now: datetime
) -> dict[PluginId, PluginConfig]:
    async with uow:
        configs = {config.plugin_id: config for config in await uow.plugin_configs.list()}
        for plugin_id, plugin_defaults in defaults.items():
            if plugin_id not in configs:
                configs[plugin_id] = _default_config(plugin_id, plugin_defaults, now)
                await uow.plugin_configs.save(configs[plugin_id])
        await uow.commit()
    return {plugin_id: configs[plugin_id] for plugin_id in defaults}


async def list_plugin_configs(uow: UnitOfWork) -> Sequence[PluginConfig]:
    async with uow:
        return await uow.plugin_configs.list()


async def set_plugin_enabled(
    uow: UnitOfWork, plugin_id: PluginId, enabled: bool, now: datetime
) -> PluginConfig:
    async with uow:
        config = await uow.plugin_configs.get(plugin_id)
        if config is None:
            raise UnknownPluginError(plugin_id)
        updated = replace(config, enabled=enabled, updated_at=now)
        await uow.plugin_configs.save(updated)
        await uow.commit()
    return updated


def _default_config(plugin_id: PluginId, defaults: PluginDefaults, now: datetime) -> PluginConfig:
    return PluginConfig(
        plugin_id=plugin_id, enabled=defaults.enabled, settings=defaults.settings, updated_at=now
    )
