import json
from collections.abc import AsyncIterator

import pytest
from httpx import ASGITransport, AsyncClient

from network_monitor_tds.application.models import PluginState, PluginStatus
from network_monitor_tds.application.plugins import get_plugin_config, sync_plugin_configs
from network_monitor_tds.application.preferences import load_presence_policy
from network_monitor_tds.domain.plugins.models import PluginId
from network_monitor_tds.plugins.host.registry import plugin_defaults
from network_monitor_tds.web.app import create_app
from network_monitor_tds.web.models import WebContext
from tests.conftest import T0, FakeControl

pytestmark = pytest.mark.anyio

DEMO = PluginId("demo")


@pytest.fixture
async def client(web_context: WebContext) -> AsyncIterator[AsyncClient]:
    await sync_plugin_configs(
        web_context.unit_of_work(), plugin_defaults(dict(web_context.plugins)), T0
    )
    transport = ASGITransport(app=create_app(web_context))
    async with AsyncClient(transport=transport, base_url="http://test") as http:
        yield http


def control(web_context: WebContext) -> FakeControl:
    assert isinstance(web_context.control, FakeControl)
    return web_context.control


async def test_settings_page(client: AsyncClient, web_context: WebContext) -> None:
    control(web_context).statuses[DEMO] = PluginStatus(PluginState.FAILING, None, "no access")

    response = await client.get("/settings")

    assert response.status_code == 200
    assert "Demo network" in response.text
    assert "Error: no access" not in response.text
    assert 'name="offline_after" value="10m"' in response.text


async def test_toggle_plugin(client: AsyncClient, web_context: WebContext) -> None:
    enabled = await client.post("/settings/plugins/demo/enabled", data={"enabled": "true"})
    disabled = await client.post("/settings/plugins/demo/enabled")

    assert json.loads(enabled.headers["HX-Trigger"]) == {"toast": "Demo network is on"}
    assert json.loads(disabled.headers["HX-Trigger"]) == {"toast": "Demo network is off"}
    assert control(web_context).reloaded == [DEMO, DEMO]
    assert not (await get_plugin_config(web_context.unit_of_work(), DEMO)).enabled


async def test_save_plugin_settings(client: AsyncClient, web_context: WebContext) -> None:
    response = await client.post("/settings/plugins/demo", data={"interval": "1m", "timeout": "5s"})

    assert json.loads(response.headers["HX-Trigger"]) == {"toast": "Saved Demo network settings"}
    config = await get_plugin_config(web_context.unit_of_work(), DEMO)
    assert config.settings == {"interval": "PT1M", "timeout": "PT5S"}
    assert control(web_context).reloaded == [DEMO]


async def test_invalid_plugin_settings_reopen_the_form(
    client: AsyncClient, web_context: WebContext
) -> None:
    response = await client.post(
        "/settings/plugins/demo", data={"interval": "soon", "timeout": "5s"}
    )

    assert "HX-Trigger" not in response.headers
    assert '<details class="cfg-wrap" open' in response.text
    assert "Use a duration like" in response.text
    assert control(web_context).reloaded == []


async def test_plugin_status(client: AsyncClient, web_context: WebContext) -> None:
    await client.post("/settings/plugins/demo/enabled", data={"enabled": "true"})
    control(web_context).statuses[DEMO] = PluginStatus(PluginState.RUNNING, None, None)

    response = await client.get("/settings/plugins/demo/status")

    assert "Running" in response.text
    assert 'hx-trigger="every 10s"' in response.text


@pytest.mark.parametrize(
    ("method", "path"),
    [("post", "/settings/plugins/nope/enabled"), ("post", "/settings/plugins/nope"), ("get", "/settings/plugins/nope/status")],
)  # fmt: skip
async def test_unknown_plugin(client: AsyncClient, method: str, path: str) -> None:
    assert (await client.request(method, path)).status_code == 404


async def test_save_presence(client: AsyncClient, web_context: WebContext) -> None:
    response = await client.post(
        "/settings/presence", data={"offline_after": "20m", "mobile_offline_after": "30m"}
    )

    assert json.loads(response.headers["HX-Trigger"]) == {"toast": "Saved presence settings"}
    policy = await load_presence_policy(web_context.unit_of_work())
    assert (policy.offline_after.total_seconds(), policy.mobile_offline_after.total_seconds()) == (
        1200,
        1800,
    )


@pytest.mark.parametrize("value", ["soon", "0s", ""])
async def test_invalid_presence_is_rejected(client: AsyncClient, value: str) -> None:
    response = await client.post(
        "/settings/presence", data={"offline_after": value, "mobile_offline_after": "30m"}
    )

    assert "HX-Trigger" not in response.headers
    assert "Use a duration like" in response.text
