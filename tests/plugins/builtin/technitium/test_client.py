import httpx
import pytest

from network_monitor_tds.plugins.builtin.technitium.client import fetch_leases
from network_monitor_tds.plugins.builtin.technitium.errors import TechnitiumError
from network_monitor_tds.plugins.builtin.technitium.schemas import Lease

pytestmark = pytest.mark.anyio

LEASES = {
    "status": "ok",
    "response": {
        "leases": [
            {
                "scope": "Default",
                "type": "Dynamic",
                "hardwareAddress": "70-85-C2-9E-04-11",
                "clientIdentifier": "1-7085C29E0411",
                "address": "192.168.1.10",
                "hostName": "homelab.lan",
                "leaseObtained": "10/03/2026 21:00:00",
                "leaseExpires": "10/04/2026 21:00:00",
            },
            {"hardwareAddress": "24-0A-C4-9F-31-5E", "address": "192.168.1.143", "hostName": None},
        ]
    },
}


def client(status: int, body: object, requests: list[httpx.Request]) -> httpx.AsyncClient:
    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        return httpx.Response(status, json=body)

    return httpx.AsyncClient(base_url="http://dns:5380", transport=httpx.MockTransport(handler))


async def test_fetch_leases() -> None:
    requests: list[httpx.Request] = []

    async with client(200, LEASES, requests) as http:
        leases = await fetch_leases(http, "s3cret")

    assert leases == [
        Lease.model_validate(
            {
                "hardwareAddress": "70-85-C2-9E-04-11",
                "address": "192.168.1.10",
                "hostName": "homelab.lan",
            }
        ),
        Lease.model_validate({"hardwareAddress": "24-0A-C4-9F-31-5E", "address": "192.168.1.143"}),
    ]
    assert str(requests[0].url) == "http://dns:5380/api/dhcp/leases/list?token=s3cret"


@pytest.mark.parametrize(
    "body", [{"status": "invalid-token"}, {"status": "error", "errorMessage": "DHCP is disabled"}]
)
async def test_fetch_leases_reports_api_errors(body: dict[str, str]) -> None:
    async with client(200, body, []) as http:
        with pytest.raises(TechnitiumError, match=body["status"]):
            await fetch_leases(http, "s3cret")


async def test_fetch_leases_reports_http_errors() -> None:
    async with client(502, {}, []) as http:
        with pytest.raises(httpx.HTTPStatusError):
            await fetch_leases(http, "s3cret")
