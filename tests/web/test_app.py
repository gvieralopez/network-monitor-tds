import json
import re
from collections.abc import AsyncIterator

import pytest
from httpx import ASGITransport, AsyncClient

from network_monitor_tds.domain.network.models import MacAddress
from network_monitor_tds.web.app import create_app
from network_monitor_tds.web.models import WebContext
from network_monitor_tds.web.templating import GROUPING_COOKIE, SORTING_COOKIE

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


@pytest.mark.usefixtures("seen_device")
@pytest.mark.parametrize(
    ("cookies", "params", "group", "sort"),
    [
        ({}, {}, "category", "smart"),
        ({GROUPING_COOKIE: "vendor", SORTING_COOKIE: "seen"}, {}, "vendor", "seen"),
        (
            {GROUPING_COOKIE: "vendor", SORTING_COOKIE: "seen"},
            {"group": "status"},
            "status",
            "seen",
        ),
        ({GROUPING_COOKIE: "sideways"}, {}, "category", "smart"),
    ],
)
async def test_devices_page_opens_with_the_browser_defaults(
    client: AsyncClient, cookies: dict[str, str], params: dict[str, str], group: str, sort: str
) -> None:
    for name, value in cookies.items():
        client.cookies.set(name, value)

    response = await client.get("/", params=params)

    assert f'<option value="{group}" selected>' in response.text
    assert f'<option value="{sort}" selected>' in response.text


async def test_devices_page_rejects_invalid_filters(client: AsyncClient) -> None:
    response = await client.get("/", params={"status": "sideways"})

    assert response.status_code == 422


async def test_dialog(client: AsyncClient, seen_device: MacAddress) -> None:
    response = await client.get(f"/devices/{seen_device}")

    assert response.status_code == 200
    assert 'id="dialog-name">esp-31f5e' in response.text
    assert 'id="tab-overview" aria-controls="panel-overview" aria-selected="true"' in response.text
    assert "Mark as known" in response.text
    assert "Forget device" in response.text
    assert "Hybrid console, two-tone" in response.text
    assert "First found by <b>Demo network</b>" in response.text


@pytest.mark.parametrize(
    ("labels", "recommended", "other"),
    [({}, "bulb", "router"), ({"category": "network"}, "router", "bulb")],
)
async def test_dialog_recommends_the_drawings_of_the_chosen_category(
    client: AsyncClient,
    seen_device: MacAddress,
    labels: dict[str, str],
    recommended: str,
    other: str,
) -> None:
    if labels:
        await client.post(f"/devices/{seen_device}/labels", data=labels)

    html = (await client.get(f"/devices/{seen_device}")).text
    recommendations = html[html.index("data-recommended") : html.index("data-others")]

    assert f'data-name="{recommended}"' in recommendations
    assert f'data-name="{other}"' not in recommendations
    assert html.count(f'data-name="{other}"') == 1


@pytest.mark.parametrize("path", ["/devices/aa:bb:cc:dd:ee:ff", "/devices/not-a-mac"])
async def test_dialog_for_unknown_device(client: AsyncClient, path: str) -> None:
    assert (await client.get(path)).status_code == 404


async def test_save_labels(client: AsyncClient, seen_device: MacAddress) -> None:
    response = await client.post(
        f"/devices/{seen_device}/labels",
        data={"name": "Garden sensor", "category": "camera", "icon": "bulb"},
    )

    assert response.status_code == 200
    assert json.loads(response.headers["HX-Trigger"]) == {"devices-changed": None, "toast": "Saved"}
    assert 'id="dialog-name">Garden sensor' in response.text
    assert 'id="tab-manage" aria-controls="panel-manage" aria-selected="true"' in response.text
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
