import json
import re
from collections.abc import AsyncIterator

import pytest
from httpx import ASGITransport, AsyncClient

from network_monitor_tds.domain.network.models import MacAddress
from network_monitor_tds.web.app import create_app
from network_monitor_tds.web.models import WebContext

pytestmark = pytest.mark.anyio

POSTER = re.compile(r'class="poster[ "]')


def posters_in(html: str) -> int:
    return len(POSTER.findall(html))


@pytest.fixture
async def client(web_context: WebContext) -> AsyncIterator[AsyncClient]:
    transport = ASGITransport(app=create_app(web_context))
    async with AsyncClient(transport=transport, base_url="http://test") as http:
        yield http


@pytest.mark.usefixtures("seen_device")
async def test_devices_page_renders_catalogue(client: AsyncClient) -> None:
    response = await client.get("/")

    assert response.status_code == 200
    assert "Network Monitor" in response.text
    assert "New on your network" in response.text
    assert posters_in(response.text) == 2
    assert "esp-31f5e" in response.text
    assert 'id="dv-chip"' in response.text
    assert 'href="#dv-chip"' in response.text
    assert 'class="ground" cx="100" cy="112" rx="32"' in response.text


@pytest.mark.usefixtures("seen_device")
@pytest.mark.parametrize(
    ("params", "posters"),
    [
        ({"q": "esp"}, 2),
        ({"q": "nothing"}, 0),
        ({"status": "offline"}, 0),
        ({"group": "none"}, 1),
        ({"group": "status", "sort": "ip"}, 1),
        ({"category": ["iot"], "new": "true", "group": "vendor"}, 2),
    ],
)
async def test_devices_page_filters(
    client: AsyncClient, params: dict[str, str | list[str]], posters: int
) -> None:
    response = await client.get("/", params=params)

    assert response.status_code == 200
    assert posters_in(response.text) == posters


async def test_devices_page_rejects_invalid_filters(client: AsyncClient) -> None:
    response = await client.get("/", params={"status": "sideways"})

    assert response.status_code == 422


async def test_drawer(client: AsyncClient, seen_device: MacAddress) -> None:
    response = await client.get(f"/devices/{seen_device}")

    assert response.status_code == 200
    assert 'id="drawer-name">esp-31f5e' in response.text
    assert "Mark as known" in response.text
    assert "Forget device" in response.text
    assert "Hybrid console, two-tone" in response.text
    assert "First found by <b>Demo network</b>" in response.text


@pytest.mark.parametrize("path", ["/devices/aa:bb:cc:dd:ee:ff", "/devices/not-a-mac"])
async def test_drawer_for_unknown_device(client: AsyncClient, path: str) -> None:
    assert (await client.get(path)).status_code == 404


async def test_save_labels(client: AsyncClient, seen_device: MacAddress) -> None:
    response = await client.post(
        f"/devices/{seen_device}/labels",
        data={"name": "Garden sensor", "category": "camera", "icon": "bulb"},
    )

    assert response.status_code == 200
    assert json.loads(response.headers["HX-Trigger"]) == {"devices-changed": None, "toast": "Saved"}
    assert 'id="drawer-name">Garden sensor' in response.text
    assert "Mark as known" not in response.text
    page = await client.get("/", params={"q": "garden"})
    assert posters_in(page.text) == 1


async def test_save_labels_rejects_unknown_icon(
    client: AsyncClient, seen_device: MacAddress
) -> None:
    response = await client.post(f"/devices/{seen_device}/labels", data={"icon": "rocket"})

    assert response.status_code == 422


async def test_acknowledge(client: AsyncClient, seen_device: MacAddress) -> None:
    response = await client.post(f"/devices/{seen_device}/acknowledge")

    assert json.loads(response.headers["HX-Trigger"])["toast"] == "Marked as known"
    assert "Mark as known" not in response.text


async def test_forget(client: AsyncClient, seen_device: MacAddress) -> None:
    response = await client.post(f"/devices/{seen_device}/forget")

    assert response.status_code == 200
    assert response.text == ""
    assert json.loads(response.headers["HX-Trigger"]) == {
        "devices-changed": None,
        "toast": "Forgot esp-31f5e",
    }
    assert (await client.get(f"/devices/{seen_device}")).status_code == 404
    assert posters_in((await client.get("/")).text) == 0


async def test_forget_unknown_device(client: AsyncClient) -> None:
    assert (await client.post("/devices/aa:bb:cc:dd:ee:ff/forget")).status_code == 404


async def test_settings_page_lists_plugins(client: AsyncClient, web_context: WebContext) -> None:
    async with web_context.unit_of_work() as uow:
        assert await uow.plugin_configs.list() == []

    empty = await client.get("/settings/plugins")

    assert empty.status_code == 200
    assert "No plugins installed." in empty.text


@pytest.mark.parametrize(
    "path", ["/static/app.css", "/static/app.js", "/static/vendor/htmx-2.0.11.min.js"]
)
async def test_static_files(client: AsyncClient, path: str) -> None:
    assert (await client.get(path)).status_code == 200
