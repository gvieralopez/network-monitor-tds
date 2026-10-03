import asyncio
from datetime import timedelta
from ipaddress import IPv4Network
from typing import ClassVar

from pydantic import Field, field_validator

from network_monitor_tds.domain.plugins.models import PluginId
from network_monitor_tds.plugins.builtin.arp.packets import arp_sighting
from network_monitor_tds.plugins.builtin.arp.sweep import sweep
from network_monitor_tds.plugins.builtin.capture.errors import NetworkTooLargeError
from network_monitor_tds.plugins.builtin.capture.interfaces import (
    interface_network,
    own_sighting,
    resolve_interface,
)
from network_monitor_tds.plugins.builtin.capture.sniffer import capture
from network_monitor_tds.plugins.builtin.capture.throttle import Throttle
from network_monitor_tds.plugins.sdk.base import ListenerPlugin, PluginContext, ScheduledPlugin
from network_monitor_tds.plugins.sdk.models import PluginInfo, PluginSettings, ScheduledSettings

MAX_SWEEP_ADDRESSES = 1024


class ArpSweepSettings(ScheduledSettings):
    interval: timedelta = timedelta(minutes=5)
    timeout: timedelta = timedelta(minutes=1)
    interface: str = ""
    subnet: str = Field(
        default="",
        description="Subnet to sweep, e.g. 192.168.1.0/24. Leave empty to use the interface's.",
    )
    reply_timeout: timedelta = Field(
        default=timedelta(seconds=3), description="How long to wait for replies after asking."
    )

    @field_validator("subnet")
    @classmethod
    def valid_subnet(cls, value: str) -> str:
        if value:
            IPv4Network(value)
        return value


class ArpListenerSettings(PluginSettings):
    interface: str = ""
    report_every: timedelta = Field(
        default=timedelta(minutes=1),
        description="Reports each device at most this often, to keep chatty devices quiet.",
    )


class ArpSweepPlugin(ScheduledPlugin[ArpSweepSettings]):
    info = PluginInfo(
        plugin_id=PluginId("arp-sweep"),
        name="ARP sweep",
        description="Asks every address in the subnet who is there.",
        enabled_by_default=True,
    )
    settings_model: ClassVar[type[ArpSweepSettings]] = ArpSweepSettings

    async def run(self, context: PluginContext) -> None:
        interface = resolve_interface(self.settings.interface)
        network = (
            IPv4Network(self.settings.subnet)
            if self.settings.subnet
            else interface_network(interface)
        )
        if network.num_addresses > MAX_SWEEP_ADDRESSES:
            raise NetworkTooLargeError(network, MAX_SWEEP_ADDRESSES)
        timeout = self.settings.reply_timeout.total_seconds()
        replies = await asyncio.to_thread(sweep, network, interface, timeout)
        for sighting in [own_sighting(interface), *replies]:
            await context.sighting(sighting.mac, sighting.ip, sighting.fields)
        context.logger.info("Swept %s on %s: %d devices", network, interface, len(replies) + 1)


class ArpListenerPlugin(ListenerPlugin[ArpListenerSettings]):
    info = PluginInfo(
        plugin_id=PluginId("arp-listen"),
        name="ARP listener",
        description="Watches ARP traffic to catch devices between sweeps.",
        enabled_by_default=True,
    )
    settings_model: ClassVar[type[ArpListenerSettings]] = ArpListenerSettings

    async def listen(self, context: PluginContext) -> None:
        throttle = Throttle(self.settings.report_every)
        async for packet in capture("arp", resolve_interface(self.settings.interface)):
            sighting = arp_sighting(packet)
            if sighting is not None and throttle.allow(sighting.mac, context.clock.now()):
                await context.sighting(sighting.mac, sighting.ip, sighting.fields)
