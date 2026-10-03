import httpx

from network_monitor_tds.plugins.builtin.technitium.errors import TechnitiumError
from network_monitor_tds.plugins.builtin.technitium.schemas import Lease, LeaseResponse

LEASES_PATH = "/api/dhcp/leases/list"
OK = "ok"


async def fetch_leases(client: httpx.AsyncClient, token: str) -> list[Lease]:
    response = await client.get(LEASES_PATH, params={"token": token})
    response.raise_for_status()
    body = LeaseResponse.model_validate_json(response.content)
    if body.status != OK or body.response is None:
        raise TechnitiumError(body.status, body.error_message)
    return body.response.leases
