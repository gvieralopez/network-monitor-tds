from datetime import timedelta
from importlib.metadata import EntryPoint

import pytest

from network_monitor_tds.domain.plugins.models import PluginDefaults, PluginId
from network_monitor_tds.plugins.builtin.demo.plugin import DemoPlugin
from network_monitor_tds.plugins.host.registry import (
    ENTRY_POINT_GROUP,
    discover_plugins,
    load_plugins,
    plugin_defaults,
)
from network_monitor_tds.plugins.sdk.errors import DuplicatePluginError

DEMO_PATH = "network_monitor_tds.plugins.builtin.demo.plugin:DemoPlugin"


def point(name: str, value: str) -> EntryPoint:
    return EntryPoint(name=name, value=value, group=ENTRY_POINT_GROUP)


def test_discovers_installed_plugins() -> None:
    assert discover_plugins()[PluginId("demo")] is DemoPlugin


@pytest.mark.parametrize(
    ("value", "message"),
    [
        ("network_monitor_tds.not_a_module:Thing", "Could not load plugin 'broken'"),
        ("network_monitor_tds.settings:AppSettings", "does not point to a Plugin subclass"),
    ],
)
def test_broken_entry_points_are_skipped(
    value: str, message: str, caplog: pytest.LogCaptureFixture
) -> None:
    plugins = load_plugins([point("broken", value), point("demo", DEMO_PATH)])

    assert plugins == {PluginId("demo"): DemoPlugin}
    assert message in caplog.text


def test_duplicate_ids_are_rejected() -> None:
    with pytest.raises(DuplicatePluginError, match="demo"):
        load_plugins([point("demo", DEMO_PATH), point("other", DEMO_PATH)])


def test_defaults_come_from_plugin_info_and_settings_model() -> None:
    defaults = plugin_defaults({PluginId("demo"): DemoPlugin})

    assert defaults == {
        PluginId("demo"): PluginDefaults(
            enabled=False,
            settings={
                "interval": _iso(timedelta(seconds=30)),
                "timeout": _iso(timedelta(seconds=10)),
            },
        )
    }


def _iso(value: timedelta) -> str:
    return f"PT{int(value.total_seconds())}S"
