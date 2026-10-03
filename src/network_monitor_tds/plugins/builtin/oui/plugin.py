from typing import ClassVar

from network_monitor_tds.domain.network.models import MacAddress
from network_monitor_tds.domain.observations.models import KnownField
from network_monitor_tds.domain.plugins.models import PluginId
from network_monitor_tds.plugins.builtin.oui.lookup import vendor_for
from network_monitor_tds.plugins.sdk.base import EnrichmentPlugin, PluginContext
from network_monitor_tds.plugins.sdk.models import PluginInfo, PluginSettings


class OuiSettings(PluginSettings):
    pass


class OuiPlugin(EnrichmentPlugin[OuiSettings]):
    info = PluginInfo(
        plugin_id=PluginId("oui"),
        name="MAC vendor lookup",
        description="Finds the manufacturer from the MAC prefix, using an offline database.",
        enabled_by_default=True,
    )
    settings_model: ClassVar[type[OuiSettings]] = OuiSettings

    async def enrich(self, context: PluginContext, mac: MacAddress) -> None:
        vendor = None if mac.is_randomized else vendor_for(mac)
        if vendor is not None:
            await context.enrichment(mac, {KnownField.VENDOR: vendor})
