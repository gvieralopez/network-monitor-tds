import pytest

from network_monitor_tds.domain.devices.identity import resolve_category, resolve_name
from network_monitor_tds.domain.devices.models import (
    NO_LABELS,
    Category,
    DeviceLabels,
    Fallback,
    Origin,
    Resolved,
)
from network_monitor_tds.domain.network.models import MacAddress
from network_monitor_tds.domain.observations.models import KnownField
from tests.conftest import FactsFactory


def test_user_label_wins(mac: MacAddress, make_facts: FactsFactory) -> None:
    labels = DeviceLabels(name="  Bedroom lamp ", category=None, icon=None)
    facts = make_facts({KnownField.LEASE_HOSTNAME: "tapo-l530"})

    assert resolve_name(mac, labels, facts) == Resolved("Bedroom lamp", Fallback.USER)


@pytest.mark.parametrize(
    ("values", "expected"),
    [
        (
            {
                KnownField.LEASE_HOSTNAME: "homelab",
                KnownField.DHCP_HOSTNAME: "dhcp-name",
                KnownField.MDNS_NAME: "mdns-name",
            },
            Resolved("homelab", KnownField.LEASE_HOSTNAME),
        ),
        (
            {KnownField.DHCP_HOSTNAME: "Pixel-8", KnownField.MDNS_NAME: "pixel.local"},
            Resolved("Pixel-8", KnownField.DHCP_HOSTNAME),
        ),
        ({KnownField.MDNS_NAME: "DS920.local."}, Resolved("DS920", KnownField.MDNS_NAME)),
        (
            {KnownField.LEASE_HOSTNAME: "amazon-FS-TV.gao.it", KnownField.DHCP_HOSTNAME: "x"},
            Resolved("amazon-FS-TV", KnownField.LEASE_HOSTNAME),
        ),
        ({KnownField.DHCP_HOSTNAME: "hive.gao.it"}, Resolved("hive", KnownField.DHCP_HOSTNAME)),
        (
            {KnownField.LEASE_HOSTNAME: "localhost.localdomain", KnownField.VENDOR: "HP"},
            Resolved("HP device", KnownField.VENDOR),
        ),
        (
            {KnownField.UPNP_FRIENDLY_NAME: "Mr. Smith's TV"},
            Resolved("Mr. Smith's TV", KnownField.UPNP_FRIENDLY_NAME),
        ),
        (
            {KnownField.UPNP_FRIENDLY_NAME: "LG webOS TV"},
            Resolved("LG webOS TV", KnownField.UPNP_FRIENDLY_NAME),
        ),
        (
            {KnownField.DHCP_HOSTNAME: "*", KnownField.MDNS_NAME: "printer.lan"},
            Resolved("printer", KnownField.MDNS_NAME),
        ),
        (
            {KnownField.LEASE_HOSTNAME: "localhost", KnownField.VENDOR: "Espressif"},
            Resolved("Espressif device", KnownField.VENDOR),
        ),
        ({}, Resolved("24:0a:c4:9f:31:5e", Fallback.MAC_ADDRESS)),
    ],
)
def test_name_priority(
    mac: MacAddress, make_facts: FactsFactory, values: dict[str, str], expected: Resolved[str]
) -> None:
    assert resolve_name(mac, NO_LABELS, make_facts(values)) == expected


def test_user_category_wins(make_facts: FactsFactory) -> None:
    labels = DeviceLabels(name=None, category=Category.MEDIA, icon=None)
    facts = make_facts({KnownField.DHCP_HOSTNAME: "iphone"})

    assert resolve_category(labels, facts) == Resolved(Category.MEDIA, Fallback.USER)


def test_category_falls_back_to_classification(make_facts: FactsFactory) -> None:
    facts = make_facts({KnownField.DHCP_HOSTNAME: "iPhone"})
    origin: Origin = KnownField.DHCP_HOSTNAME

    assert resolve_category(NO_LABELS, facts) == Resolved(Category.PHONE, origin)
