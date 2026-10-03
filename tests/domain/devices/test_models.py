from datetime import timedelta
from ipaddress import IPv4Address

import pytest

from network_monitor_tds.domain.devices.errors import InvalidDeviceTimelineError, InvalidLabelError
from network_monitor_tds.domain.devices.models import (
    NO_LABELS,
    Category,
    ClassificationRule,
    Device,
    DeviceLabels,
)
from network_monitor_tds.domain.errors import NaiveDatetimeError
from network_monitor_tds.domain.network.models import MacAddress
from tests.conftest import NAIVE, T0


@pytest.mark.parametrize(
    ("category", "mobile"),
    [
        (Category.PHONE, True),
        (Category.TABLET, True),
        (Category.SERVER, False),
        (Category.UNKNOWN, False),
    ],
)
def test_category_is_mobile(category: Category, mobile: bool) -> None:
    assert category.is_mobile is mobile


@pytest.mark.parametrize(("name", "icon"), [("  ", None), (None, ""), ("", "plug")])
def test_labels_reject_blank_values(name: str | None, icon: str | None) -> None:
    with pytest.raises(InvalidLabelError):
        DeviceLabels(name=name, category=None, icon=icon)


def test_discovered_device_is_new_and_unlabelled(mac: MacAddress, ip: IPv4Address) -> None:
    device = Device.discovered(mac, ip, T0)

    assert device.first_seen == device.last_seen == T0
    assert device.acknowledged is False
    assert device.labels == NO_LABELS


def test_device_rejects_last_seen_before_first_seen(mac: MacAddress) -> None:
    with pytest.raises(InvalidDeviceTimelineError):
        Device(
            mac=mac,
            ip=None,
            first_seen=T0,
            last_seen=T0 - timedelta(seconds=1),
            acknowledged=False,
            labels=NO_LABELS,
        )


def test_device_requires_aware_timestamps(mac: MacAddress) -> None:
    with pytest.raises(NaiveDatetimeError):
        Device(
            mac=mac,
            ip=None,
            first_seen=NAIVE,
            last_seen=NAIVE,
            acknowledged=False,
            labels=NO_LABELS,
        )


@pytest.mark.parametrize(
    ("new_ip", "expected_ip"),
    [
        (IPv4Address("192.168.1.200"), IPv4Address("192.168.1.200")),
        (None, IPv4Address("192.168.1.143")),
    ],
)
def test_seen_updates_last_seen_and_ip(
    mac: MacAddress, ip: IPv4Address, new_ip: IPv4Address | None, expected_ip: IPv4Address
) -> None:
    later = T0 + timedelta(minutes=5)

    device = Device.discovered(mac, ip, T0).seen(new_ip, later)

    assert device.last_seen == later
    assert device.ip == expected_ip


def test_seen_ignores_out_of_order_sightings(mac: MacAddress, ip: IPv4Address) -> None:
    device = Device.discovered(mac, ip, T0)

    assert device.seen(IPv4Address("10.0.0.1"), T0 - timedelta(minutes=1)) is device


def test_acknowledge(mac: MacAddress, ip: IPv4Address) -> None:
    assert Device.discovered(mac, ip, T0).acknowledge().acknowledged is True


def test_relabel_sets_labels_and_acknowledges(mac: MacAddress, ip: IPv4Address) -> None:
    labels = DeviceLabels(name="Bedroom lamp", category=Category.IOT, icon="bulb")

    device = Device.discovered(mac, ip, T0).relabel(labels)

    assert device.labels == labels
    assert device.acknowledged is True


TV_RULE = ClassificationRule(Category.MEDIA, fragments=("firetv", "webos"), words=("tv",))


@pytest.mark.parametrize(
    ("text", "matches"),
    [
        ("Fire-TV-Stick", True),
        ("fire_tv", True),
        ("LG webOS TV", True),
        ("living-room-tv", True),
        ("TV", True),
        ("tvheadend", False),
        ("tv2", False),
        ("printer", False),
        ("", False),
    ],
)
def test_classification_rule_matches(text: str, matches: bool) -> None:
    assert TV_RULE.matches(text) is matches
