import logging
from abc import ABC, abstractmethod
from collections.abc import Awaitable, Callable, Mapping
from dataclasses import dataclass
from ipaddress import IPv4Address
from typing import ClassVar

from network_monitor_tds.domain.network.models import MacAddress
from network_monitor_tds.domain.observations.models import Observation, ObservationKind
from network_monitor_tds.domain.plugins.models import PluginId
from network_monitor_tds.domain.time import Clock
from network_monitor_tds.plugins.sdk.models import (
    PluginInfo,
    PluginKind,
    PluginSettings,
    ScheduledSettings,
)

type Emit = Callable[[Observation], Awaitable[None]]


@dataclass(frozen=True, slots=True)
class PluginContext:
    plugin_id: PluginId
    clock: Clock
    emit: Emit
    logger: logging.Logger

    async def sighting(
        self, mac: MacAddress, ip: IPv4Address | None, fields: Mapping[str, str]
    ) -> None:
        await self._report(ObservationKind.SIGHTING, mac, ip, fields)

    async def enrichment(self, mac: MacAddress, fields: Mapping[str, str]) -> None:
        await self._report(ObservationKind.ENRICHMENT, mac, None, fields)

    async def _report(
        self,
        kind: ObservationKind,
        mac: MacAddress,
        ip: IPv4Address | None,
        fields: Mapping[str, str],
    ) -> None:
        observation = Observation(
            source=self.plugin_id,
            kind=kind,
            mac=mac,
            ip=ip,
            observed_at=self.clock.now(),
            fields=fields,
        )
        await self.emit(observation)


class Plugin[S: PluginSettings](ABC):
    info: ClassVar[PluginInfo]
    kind: ClassVar[PluginKind]
    settings_model: ClassVar[type[PluginSettings]]

    def __init__(self, settings: S) -> None:
        self.settings = settings


class ListenerPlugin[S: PluginSettings](Plugin[S]):
    kind = PluginKind.LISTENER

    @abstractmethod
    async def listen(self, context: PluginContext) -> None: ...


class ScheduledPlugin[S: ScheduledSettings](Plugin[S]):
    kind = PluginKind.SCHEDULED

    @abstractmethod
    async def run(self, context: PluginContext) -> None: ...


class EnrichmentPlugin[S: PluginSettings](Plugin[S]):
    kind = PluginKind.ENRICHMENT

    @abstractmethod
    async def enrich(self, context: PluginContext, mac: MacAddress) -> None: ...
