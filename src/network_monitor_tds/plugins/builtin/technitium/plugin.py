from datetime import timedelta
from typing import ClassVar

import httpx
from pydantic import Field, field_validator

from network_monitor_tds.domain.network.errors import InvalidMacAddressError
from network_monitor_tds.domain.network.models import MacAddress
from network_monitor_tds.domain.observations.models import KnownField
from network_monitor_tds.domain.plugins.models import PluginId
from network_monitor_tds.plugins.builtin.technitium.client import fetch_leases
from network_monitor_tds.plugins.builtin.technitium.schemas import Lease
from network_monitor_tds.plugins.sdk.base import PluginContext, ScheduledPlugin
from network_monitor_tds.plugins.sdk.models import PluginInfo, PluginPurpose, ScheduledSettings


class TechnitiumSettings(ScheduledSettings):
    interval: timedelta = Field(
        default=timedelta(minutes=5),
        title="Import leases every",
        description="How often to read the leases from Technitium.",
    )
    timeout: timedelta = timedelta(seconds=30)
    url: str = Field(
        default="",
        title="Server address",
        description="Technitium web console, e.g. http://192.168.1.10:5380",
    )
    token: str = Field(
        default="",
        repr=False,
        title="API token",
        description="Create one in Technitium under Administration, Sessions.",
    )
    verify_tls: bool = Field(
        default=True,
        title="Verify TLS certificate",
        description="Turn off only for self-signed certificates on HTTPS.",
    )

    @classmethod
    def setup_fields(cls) -> frozenset[str]:
        return frozenset({"url", "token"})

    @field_validator("url")
    @classmethod
    def http_url(cls, value: str) -> str:
        if value and not value.startswith(("http://", "https://")):
            message = "url must start with http:// or https://"
            raise ValueError(message)
        return value.rstrip("/")


class TechnitiumPlugin(ScheduledPlugin[TechnitiumSettings]):
    info = PluginInfo(
        plugin_id=PluginId("technitium"),
        name="Technitium DHCP leases",
        description="Imports lease hostnames from the Technitium DNS Server API.",
        enabled_by_default=False,
        purpose=PluginPurpose.INTEGRATION,
    )
    settings_model: ClassVar[type[TechnitiumSettings]] = TechnitiumSettings

    async def run(self, context: PluginContext) -> None:
        if not (self.settings.url and self.settings.token):
            context.logger.warning("Set url and token to import leases from Technitium")
            return
        async with create_client(self.settings) as client:
            leases = await fetch_leases(client, self.settings.token)
        for lease in leases:
            await _report(context, lease)
        context.logger.info("Imported %d leases", len(leases))


def create_client(settings: TechnitiumSettings) -> httpx.AsyncClient:
    return httpx.AsyncClient(
        base_url=settings.url, verify=settings.verify_tls, timeout=settings.timeout.total_seconds()
    )


async def _report(context: PluginContext, lease: Lease) -> None:
    try:
        mac = MacAddress.parse(lease.hardware_address)
    except InvalidMacAddressError:
        context.logger.warning("Skipping a lease with an unreadable MAC address")
        return
    if lease.host_name:
        await context.enrichment(mac, {KnownField.LEASE_HOSTNAME: lease.host_name})
