from dataclasses import replace
from datetime import timedelta
from ipaddress import IPv4Address

import pytest

from network_monitor_tds.application.models import DeviceSummary
from network_monitor_tds.domain.devices.models import Category, Device, Fallback, Resolved
from network_monitor_tds.domain.network.models import MacAddress
from network_monitor_tds.domain.observations.models import KnownField
from network_monitor_tds.web.pages.board import (
    BoardQuery,
    Grouping,
    Sorting,
    StatusFilter,
    build_board,
    vendor_label,
)
from tests.conftest import T0


def summary(
    name: str,
    mac: str,
    category: Category,
    online: bool,
    is_new: bool,
    vendor: str | None,
    ip: str,
    last_seen_minutes_ago: int,
) -> DeviceSummary:
    device = Device(
        mac=MacAddress.parse(mac),
        ip=IPv4Address(ip),
        first_seen=T0 - timedelta(days=1),
        last_seen=T0 - timedelta(minutes=last_seen_minutes_ago),
        acknowledged=not is_new,
        labels=Device.discovered(MacAddress.parse(mac), None, T0).labels,
    )
    return DeviceSummary(
        device=device,
        name=Resolved(name, KnownField.DHCP_HOSTNAME),
        category=Resolved(category, Fallback.DEFAULT),
        vendor=vendor,
        online=online,
        last_24_hours=(online,) * 24,
    )


LAPTOP = summary(
    "ThinkPad", "8c:8c:aa:31:f0:62", Category.COMPUTER, False, False, "Lenovo", "192.168.1.21", 120
)
NAS = summary(
    "NAS", "00:11:32:c4:7e:92", Category.SERVER, True, False, "Synology", "192.168.1.12", 0
)
PHONE = summary("Pixel", "3a:f1:5c:22:9b:07", Category.PHONE, True, True, None, "192.168.1.30", 0)
LAB = summary("homelab", "70:85:c2:9e:04:11", Category.SERVER, True, False, None, "192.168.1.10", 0)
DEVICES = [LAPTOP, NAS, PHONE, LAB]  # fmt: skip


def names(query: BoardQuery) -> list[list[str]]:
    board = build_board(DEVICES, query)
    return [[device.name.value for device in shelf.devices] for shelf in board.shelves]


def titles(query: BoardQuery) -> list[str]:
    return [shelf.title for shelf in build_board(DEVICES, query).shelves]


@pytest.mark.parametrize(
    ("query", "expected"),
    [
        (BoardQuery(group=Grouping.NONE), [["Pixel", "homelab", "NAS", "ThinkPad"]]),
        (BoardQuery(group=Grouping.NONE, sort=Sorting.NAME), [["homelab", "NAS", "Pixel", "ThinkPad"]]),
        (BoardQuery(group=Grouping.NONE, sort=Sorting.IP), [["homelab", "NAS", "ThinkPad", "Pixel"]]),
        (BoardQuery(group=Grouping.NONE, sort=Sorting.SEEN), [["homelab", "NAS", "Pixel", "ThinkPad"]]),
        (BoardQuery(group=Grouping.NONE, status=StatusFilter.OFFLINE), [["ThinkPad"]]),
        (BoardQuery(group=Grouping.NONE, status=StatusFilter.ONLINE, sort=Sorting.NAME), [["homelab", "NAS", "Pixel"]]),
        (BoardQuery(group=Grouping.NONE, new=True), [["Pixel"]]),
        (BoardQuery(group=Grouping.NONE, category=[Category.SERVER], sort=Sorting.NAME), [["homelab", "NAS"]]),
        (BoardQuery(group=Grouping.NONE, q="192.168.1.2"), [["ThinkPad"]]),
        (BoardQuery(group=Grouping.NONE, q=" synology "), [["NAS"]]),
        (BoardQuery(group=Grouping.NONE, q="3a:f1"), [["Pixel"]]),
        (BoardQuery(group=Grouping.NONE, q="phone"), [["Pixel"]]),
        (BoardQuery(q="nothing matches"), []),
    ],
)  # fmt: skip
def test_filters_and_sorting(query: BoardQuery, expected: list[list[str]]) -> None:
    assert names(query) == expected


@pytest.mark.parametrize(
    ("grouping", "expected"),
    [
        (Grouping.CATEGORY, ["New on your network", "Server", "Computer", "Phone"]),
        (Grouping.STATUS, ["New", "Online", "Offline"]),
        (Grouping.VENDOR, ["New on your network", "Lenovo", "Synology", "Private MAC", "Unknown vendor"]),
    ],
)  # fmt: skip
def test_grouping(grouping: Grouping, expected: list[str]) -> None:
    assert titles(BoardQuery(group=grouping)) == expected


def test_category_shelves_carry_their_category() -> None:
    shelves = build_board(DEVICES, BoardQuery()).shelves

    assert [shelf.category for shelf in shelves] == [
        None,
        Category.SERVER,
        Category.COMPUTER,
        Category.PHONE,
    ]
    assert shelves[0].spotlight is True
    assert shelves[1].online == 2


@pytest.mark.parametrize(
    ("device", "label"),
    [(NAS, "Synology"), (PHONE, "Private MAC"), (replace(LAB, vendor=None), "Unknown vendor")],
)
def test_vendor_label(device: DeviceSummary, label: str) -> None:
    assert vendor_label(device) == label


@pytest.mark.parametrize(
    ("query", "filtered"),
    [
        (BoardQuery(), False),
        (BoardQuery(group=Grouping.VENDOR, sort=Sorting.IP), False),
        (BoardQuery(q="nas"), True),
        (BoardQuery(new=True), True),
        (BoardQuery(category=[Category.IOT]), True),
        (BoardQuery(status=StatusFilter.ONLINE), True),
    ],
)
def test_is_filtered(query: BoardQuery, filtered: bool) -> None:
    assert query.is_filtered is filtered
