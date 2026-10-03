import httpx
import pytest
from pydantic import ValidationError

from network_monitor_tds.domain.network.models import MacAddress
from network_monitor_tds.domain.observations.models import KnownField, ObservationKind
from network_monitor_tds.plugins.builtin.technitium import plugin
from network_monitor_tds.plugins.builtin.technitium.plugin import (
    TechnitiumPlugin,
    TechnitiumSettings,
)
from tests.conftest import RecordingEmit, plugin_context
from tests.plugins.builtin.technitium.test_client import LEASES

pytestmark = pytest.mark.anyio

CONFIGURED = TechnitiumSettings(url="http://dns:5380/", token="s3cret")


def serve(monkeypatch: pytest.MonkeyPatch, body: object) -> None:
    transport = httpx.MockTransport(lambda _request: httpx.Response(200, json=body))
    monkeypatch.setattr(
        plugin,
        "create_client",
        lambda settings: httpx.AsyncClient(base_url=settings.url, transport=transport),
    )


async def test_imports_lease_hostnames(monkeypatch: pytest.MonkeyPatch) -> None:
    serve(monkeypatch, LEASES)
    emit = RecordingEmit()

    await TechnitiumPlugin(CONFIGURED).run(plugin_context("technitium", emit))

    [observation] = emit.observations
    assert observation.mac == MacAddress.parse("70:85:c2:9e:04:11")
    assert observation.kind is ObservationKind.ENRICHMENT
    assert observation.fields == {KnownField.LEASE_HOSTNAME: "homelab.lan"}


async def test_skips_unreadable_mac_addresses(
    monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    body = {
        "status": "ok",
        "response": {"leases": [{"hardwareAddress": "??", "address": "1.2.3.4", "hostName": "x"}]},
    }
    serve(monkeypatch, body)
    emit = RecordingEmit()

    await TechnitiumPlugin(CONFIGURED).run(plugin_context("technitium", emit))

    assert emit.observations == []
    assert "unreadable MAC address" in caplog.text


async def test_does_nothing_until_configured(caplog: pytest.LogCaptureFixture) -> None:
    emit = RecordingEmit()

    await TechnitiumPlugin(TechnitiumSettings()).run(plugin_context("technitium", emit))

    assert emit.observations == []
    assert "Set url and token" in caplog.text


def test_settings() -> None:
    assert CONFIGURED.url == "http://dns:5380"
    assert "s3cret" not in repr(CONFIGURED)
    assert TechnitiumSettings.secret_fields() == {"token"}
    with pytest.raises(ValidationError):
        TechnitiumSettings(url="dns:5380")


async def test_create_client_uses_settings() -> None:
    async with plugin.create_client(CONFIGURED) as http:
        assert str(http.base_url) == "http://dns:5380"
        assert http.timeout.read == 30
