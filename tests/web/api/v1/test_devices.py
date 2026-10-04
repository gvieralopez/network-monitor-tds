from collections.abc import AsyncIterator

import pytest
from httpx import ASGITransport, AsyncClient

from network_monitor_tds.domain.devices.models import Device
from network_monitor_tds.domain.network.models import MacAddress
from network_monitor_tds.web.app import create_app
from network_monitor_tds.web.models import WebContext
from tests.conftest import T0, Database

pytestmark = pytest.mark.anyio

PRINTER = MacAddress.parse("00:1b:a9:44:02:7c")
ESP = {
    "mac": "24:0a:c4:9f:31:5e",
    "ip": "192.168.1.143",
    "name": "esp-31f5e",
    "category": "iot",
    "vendor": None,
    "online": True,
    "new": True,
    "first_seen": "2026-10-03T12:00:00Z",
    "last_seen": "2026-10-03T12:00:00Z",
}
OFFLINE_PRINTER = {
    "mac": "00:1b:a9:44:02:7c",
    "ip": None,
    "name": "00:1b:a9:44:02:7c",
    "category": "unknown",
    "vendor": None,
    "online": False,
    "new": True,
    "first_seen": "2026-10-03T12:00:00Z",
    "last_seen": "2026-10-03T12:00:00Z",
}


@pytest.fixture
async def client(web_context: WebContext) -> AsyncIterator[AsyncClient]:
    transport = ASGITransport(app=create_app(web_context))
    async with AsyncClient(transport=transport, base_url="http://test") as http:
        yield http


@pytest.fixture
async def offline_device(database: Database) -> MacAddress:
    async with database.unit_of_work() as uow:
        await uow.devices.save(Device.discovered(PRINTER, None, T0))
        await uow.commit()
    return PRINTER


@pytest.mark.usefixtures("seen_device", "offline_device")
@pytest.mark.parametrize(
    ("path", "expected"),
    [("/api/v1/devices", [OFFLINE_PRINTER, ESP]), ("/api/v1/devices/online", [ESP])],
)
async def test_devices(client: AsyncClient, path: str, expected: list[dict[str, object]]) -> None:
    response = await client.get(path)

    assert response.status_code == 200
    assert response.json() == expected


@pytest.mark.parametrize("path", ["/api/v1/devices", "/api/v1/devices/online"])
async def test_devices_when_none_are_known(client: AsyncClient, path: str) -> None:
    assert (await client.get(path)).json() == []
