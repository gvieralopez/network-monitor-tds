import pytest

from network_monitor_tds.domain.errors import NaiveDatetimeError
from network_monitor_tds.domain.plugins.models import PluginConfig, PluginId
from tests.conftest import NAIVE


def test_plugin_config_requires_aware_timestamp() -> None:
    with pytest.raises(NaiveDatetimeError):
        PluginConfig(plugin_id=PluginId("oui"), enabled=True, settings={}, updated_at=NAIVE)
