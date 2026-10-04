import logging
from ipaddress import IPv4Address

import pytest

from network_monitor_tds.domain.network.models import MacAddress
from network_monitor_tds.domain.observations.models import KnownField, Observation, ObservationKind
from network_monitor_tds.plugins.sdk.base import PluginContext
from tests.conftest import DHCP_SNIFF, T0, FixedClock, no_known_devices

pytestmark = pytest.mark.anyio


class Collector:
    def __init__(self) -> None:
        self.observations: list[Observation] = []

    async def __call__(self, observation: Observation) -> None:
        self.observations.append(observation)


def context(collector: Collector) -> PluginContext:
    return PluginContext(
        DHCP_SNIFF, FixedClock(T0), collector, logging.getLogger("tests"), no_known_devices
    )


async def test_sighting_builds_observation(mac: MacAddress, ip: IPv4Address) -> None:
    collector = Collector()

    await context(collector).sighting(mac, ip, {KnownField.DHCP_HOSTNAME: "esp"})

    assert collector.observations == [
        Observation(DHCP_SNIFF, ObservationKind.SIGHTING, mac, ip, T0, {"dhcp_hostname": "esp"})
    ]


async def test_enrichment_builds_observation_without_ip(mac: MacAddress) -> None:
    collector = Collector()

    await context(collector).enrichment(mac, {KnownField.VENDOR: "Espressif"})

    assert collector.observations == [
        Observation(DHCP_SNIFF, ObservationKind.ENRICHMENT, mac, None, T0, {"vendor": "Espressif"})
    ]
