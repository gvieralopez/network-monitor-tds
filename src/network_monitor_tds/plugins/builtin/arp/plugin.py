import asyncio
from datetime import datetime, timedelta
from ipaddress import IPv4Address, IPv4Network
from typing import ClassVar

from pydantic import Field, field_validator

from network_monitor_tds.domain.plugins.models import PluginId
from network_monitor_tds.plugins.builtin.arp.packets import ARP_FILTER, arp_sighting
from network_monitor_tds.plugins.builtin.arp.sweep import (
    SweepTargets,
    quiet_addresses,
    sweep,
    target_count,
)
from network_monitor_tds.plugins.builtin.capture.errors import NetworkTooLargeError
from network_monitor_tds.plugins.builtin.capture.interfaces import (
    interface_network,
    own_sighting,
    resolve_interface,
)
from network_monitor_tds.plugins.builtin.capture.models import Sighting
from network_monitor_tds.plugins.builtin.capture.sniffer import capture
from network_monitor_tds.plugins.builtin.capture.throttle import Throttle
from network_monitor_tds.plugins.sdk.base import ListenerPlugin, PluginContext, ScheduledPlugin
from network_monitor_tds.plugins.sdk.models import PluginInfo, PluginSettings, ScheduledSettings

MAX_SWEEP_ADDRESSES = 1024
QUIET_FRACTION_OF_INTERVAL = 0.5


class ArpSweepSettings(ScheduledSettings):
    interval: timedelta = Field(
        default=timedelta(minutes=5),
        description="How often to ask devices that have gone quiet whether they are still there.",
    )
    full_sweep_every: timedelta = Field(
        default=timedelta(minutes=30),
        description="How often to ask every address in the subnet, to find new devices.",
    )
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
        description="Asks quiet devices whether they are still there, and the whole subnet "
        "every so often.",
        enabled_by_default=True,
    )
    settings_model: ClassVar[type[ArpSweepSettings]] = ArpSweepSettings

    def __init__(self, settings: ArpSweepSettings) -> None:
        super().__init__(settings)
        self._last_full_sweep: datetime | None = None

    async def run(self, context: PluginContext) -> None:
        interface = resolve_interface(self.settings.interface)
        network = (
            IPv4Network(self.settings.subnet)
            if self.settings.subnet
            else interface_network(interface)
        )
        if network.num_addresses > MAX_SWEEP_ADDRESSES:
            raise NetworkTooLargeError(network, MAX_SWEEP_ADDRESSES)
        now = context.clock.now()
        full = self._full_sweep_due(now)
        targets = network if full else await self._quiet_targets(context, network, now)
        replies = await self._ask(targets, interface)
        if full:
            self._last_full_sweep = now
        for sighting in [own_sighting(interface), *replies]:
            await context.sighting(sighting.mac, sighting.ip, sighting.fields)
        context.logger.info(
            "%s sweep of %s on %s: %d asked, %d answered",
            "Full" if full else "Targeted",
            network,
            interface,
            target_count(targets),
            len(replies),
        )

    def _full_sweep_due(self, now: datetime) -> bool:
        last = self._last_full_sweep
        return last is None or now - last >= self.settings.full_sweep_every

    async def _quiet_targets(
        self, context: PluginContext, network: IPv4Network, now: datetime
    ) -> list[IPv4Address]:
        devices = await context.known_devices()
        quiet_since = now - self.settings.interval * QUIET_FRACTION_OF_INTERVAL
        gone_since = now - self.settings.full_sweep_every
        return quiet_addresses(devices, network, quiet_since, gone_since)

    async def _ask(self, targets: SweepTargets, interface: str) -> list[Sighting]:
        if not targets:
            return []
        timeout = self.settings.reply_timeout.total_seconds()
        return await asyncio.to_thread(sweep, targets, interface, timeout)


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
        async for packet in capture(ARP_FILTER, resolve_interface(self.settings.interface)):
            sighting = arp_sighting(packet)
            if sighting is not None and throttle.allow(sighting.mac, context.clock.now()):
                await context.sighting(sighting.mac, sighting.ip, sighting.fields)
