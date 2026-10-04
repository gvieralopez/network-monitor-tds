import pytest

from network_monitor_tds.domain.network.models import MacAddress
from network_monitor_tds.domain.observations.models import ObservationKind
from network_monitor_tds.plugins.builtin.oui.plugin import OuiPlugin, OuiSettings
from tests.conftest import RecordingEmit, plugin_context

pytestmark = pytest.mark.anyio


@pytest.mark.parametrize(
    ("mac", "vendors"),
    [("24:0a:c4:9f:31:5e", ["Espressif"]), ("3a:f1:5c:22:9b:07", []), ("00:00:01:00:00:00", ["XEROX"])],
)  # fmt: skip
async def test_enrich_reports_vendor(mac: str, vendors: list[str]) -> None:
    emit = RecordingEmit()

    await OuiPlugin(OuiSettings()).enrich(plugin_context("oui", emit), MacAddress.parse(mac))

    assert [o.fields["vendor"] for o in emit.observations] == vendors
    assert all(o.kind is ObservationKind.ENRICHMENT for o in emit.observations)
