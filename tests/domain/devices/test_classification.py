import pytest

from network_monitor_tds.domain.devices.classification import classify
from network_monitor_tds.domain.devices.models import Category, Fallback, Origin
from network_monitor_tds.domain.observations.models import KnownField
from tests.conftest import FactsFactory


@pytest.mark.parametrize(
    ("hostname", "category"),
    [
        ("iPad", Category.TABLET),
        ("Galaxy-Tab-S9", Category.TABLET),
        ("iPhone", Category.PHONE),
        ("android-7f3a2c9e", Category.PHONE),
        ("Pixel-8", Category.PHONE),
        ("ThinkPad-X1", Category.COMPUTER),
        ("gustavo-pc", Category.COMPUTER),
        ("Mac", Category.COMPUTER),
        ("Johns-MBP", Category.COMPUTER),
        ("Watch", Category.PHONE),
        ("Chromecast", Category.MEDIA),
        ("LG webOS TV", Category.MEDIA),
        ("living-room-tv", Category.MEDIA),
        ("PS5-7A2D", Category.MEDIA),
        ("HP LaserJet M110w", Category.PRINTER),
        ("front-door-cam", Category.CAMERA),
        ("shellyplug-s-3C8A1F", Category.IOT),
        ("esp-31f5e", Category.IOT),
        ("roborock-vacuum-s7", Category.IOT),
        ("DiskStation", Category.SERVER),
        ("raspberrypi", Category.SERVER),
        ("homelab", Category.SERVER),
        ("deco-hallway", Category.NETWORK),
    ],
)
def test_hostname_rules(make_facts: FactsFactory, hostname: str, category: Category) -> None:
    resolved = classify(make_facts({KnownField.DHCP_HOSTNAME: hostname}))

    assert resolved.value is category
    assert resolved.origin is KnownField.DHCP_HOSTNAME


@pytest.mark.parametrize(
    ("values", "category", "origin"),
    [
        ({KnownField.MDNS_SERVICES: "_googlecast._tcp"}, Category.MEDIA, KnownField.MDNS_SERVICES),
        (
            {KnownField.MDNS_SERVICES: "_ipp._tcp, _pdl-datastream._tcp"},
            Category.PRINTER,
            KnownField.MDNS_SERVICES,
        ),
        (
            {KnownField.MDNS_SERVICES: "_apple-mobdev2._tcp, _airplay._tcp"},
            Category.PHONE,
            KnownField.MDNS_SERVICES,
        ),
        (
            {KnownField.DHCP_VENDOR_CLASS: "android-dhcp-14"},
            Category.PHONE,
            KnownField.DHCP_VENDOR_CLASS,
        ),
        (
            {KnownField.DHCP_VENDOR_CLASS: "MSFT 5.0"},
            Category.COMPUTER,
            KnownField.DHCP_VENDOR_CLASS,
        ),
        ({KnownField.VENDOR: "Espressif Inc."}, Category.IOT, KnownField.VENDOR),
        ({KnownField.VENDOR: "Synology Incorporated"}, Category.SERVER, KnownField.VENDOR),
        ({KnownField.VENDOR: "Sony Interactive Entertainment"}, Category.MEDIA, KnownField.VENDOR),
        ({KnownField.VENDOR: "FRITZ! Technology"}, Category.NETWORK, KnownField.VENDOR),
        ({KnownField.VENDOR: "Amazon Technologies"}, Category.MEDIA, KnownField.VENDOR),
        (
            {KnownField.VENDOR: "CLOUD NETWORK TECHNOLOGY SINGAPORE"},
            Category.COMPUTER,
            KnownField.VENDOR,
        ),
        ({KnownField.VENDOR: "GIGA-BYTE TECHNOLOGY"}, Category.COMPUTER, KnownField.VENDOR),
        ({KnownField.VENDOR: "Micro-Star INTL"}, Category.COMPUTER, KnownField.VENDOR),
        ({KnownField.VENDOR: "Lenovo"}, Category.UNKNOWN, Fallback.DEFAULT),
        ({}, Category.UNKNOWN, Fallback.DEFAULT),
    ],
)
def test_non_hostname_rules(
    make_facts: FactsFactory, values: dict[str, str], category: Category, origin: Origin
) -> None:
    resolved = classify(make_facts(values))

    assert resolved.value is category
    assert resolved.origin == origin


def test_hostname_takes_precedence_over_vendor(make_facts: FactsFactory) -> None:
    facts = make_facts({KnownField.DHCP_HOSTNAME: "front-door-cam", KnownField.VENDOR: "Espressif"})

    assert classify(facts).value is Category.CAMERA


def test_amazon_vendor_gives_way_to_a_kindle_hostname(make_facts: FactsFactory) -> None:
    facts = make_facts(
        {KnownField.DHCP_HOSTNAME: "Kindle-Paperwhite", KnownField.VENDOR: "Amazon Technologies"}
    )

    assert classify(facts).value is Category.TABLET
