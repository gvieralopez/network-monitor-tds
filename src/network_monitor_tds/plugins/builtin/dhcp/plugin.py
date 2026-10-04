from typing import ClassVar

from network_monitor_tds.domain.plugins.models import PluginId
from network_monitor_tds.plugins.builtin.capture.interfaces import resolve_interface
from network_monitor_tds.plugins.builtin.capture.sniffer import capture
from network_monitor_tds.plugins.builtin.dhcp.packets import DHCP_FILTER, dhcp_sighting
from network_monitor_tds.plugins.sdk.base import ListenerPlugin, PluginContext
from network_monitor_tds.plugins.sdk.models import PluginInfo, PluginPurpose, PluginSettings


class DhcpSnifferSettings(PluginSettings):
    interface: str = ""


class DhcpSnifferPlugin(ListenerPlugin[DhcpSnifferSettings]):
    info = PluginInfo(
        plugin_id=PluginId("dhcp-sniff"),
        name="DHCP sniffer",
        description="Reads DHCP broadcasts for hostnames and device fingerprints.",
        enabled_by_default=True,
        purpose=PluginPurpose.PASSIVE_DISCOVERY,
    )
    settings_model: ClassVar[type[DhcpSnifferSettings]] = DhcpSnifferSettings

    async def listen(self, context: PluginContext) -> None:
        async for packet in capture(DHCP_FILTER, resolve_interface(self.settings.interface)):
            sighting = dhcp_sighting(packet)
            if sighting is not None:
                await context.sighting(sighting.mac, sighting.ip, sighting.fields)
