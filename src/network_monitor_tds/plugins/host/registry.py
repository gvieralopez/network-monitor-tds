import logging
from collections.abc import Iterable
from importlib.metadata import EntryPoint, entry_points
from typing import Any

from network_monitor_tds.domain.plugins.models import PluginDefaults, PluginId
from network_monitor_tds.plugins.sdk.base import Plugin
from network_monitor_tds.plugins.sdk.errors import DuplicatePluginError

logger = logging.getLogger(__name__)

ENTRY_POINT_GROUP = "network_monitor_tds.plugins"

type PluginClass = type[Plugin[Any]]


def discover_plugins() -> dict[PluginId, PluginClass]:
    return load_plugins(entry_points(group=ENTRY_POINT_GROUP))


def load_plugins(points: Iterable[EntryPoint]) -> dict[PluginId, PluginClass]:
    plugins: dict[PluginId, PluginClass] = {}
    for point in points:
        plugin = _load(point)
        if plugin is None:
            continue
        plugin_id = plugin.info.plugin_id
        if plugin_id in plugins:
            raise DuplicatePluginError(plugin_id)
        plugins[plugin_id] = plugin
    return plugins


def plugin_defaults(plugins: dict[PluginId, PluginClass]) -> dict[PluginId, PluginDefaults]:
    return {
        plugin_id: PluginDefaults(
            enabled=plugin.info.enabled_by_default,
            settings=plugin.settings_model().model_dump(mode="json"),
        )
        for plugin_id, plugin in plugins.items()
    }


def _load(point: EntryPoint) -> PluginClass | None:
    try:
        plugin = point.load()
    except Exception:
        logger.exception("Could not load plugin %r", point.name)
        return None
    if not (isinstance(plugin, type) and issubclass(plugin, Plugin)):
        logger.error("Entry point %r does not point to a Plugin subclass", point.name)
        return None
    return plugin
