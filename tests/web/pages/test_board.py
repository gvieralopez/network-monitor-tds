from dataclasses import replace
from datetime import timedelta
from ipaddress import IPv4Address

import pytest

from network_monitor_tds.application.models import DeviceSummary
from network_monitor_tds.domain.devices.models import Category, Device, Fallback, Resolved
from network_monitor_tds.domain.network.models import MacAddress
from network_monitor_tds.domain.observations.models import KnownField
from network_monitor_tds.web.pages.board import (
    AppliedFilter,
    BoardQuery,
    Grouping,
    Sorting,
    SortOrder,
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
    first_seen_days_ago: int,
) -> DeviceSummary:
    device = Device(
        mac=MacAddress.parse(mac),
        ip=IPv4Address(ip),
        first_seen=T0 - timedelta(days=first_seen_days_ago),
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
    "ThinkPad",
    "8c:8c:aa:31:f0:62",
    Category.COMPUTER,
    False,
    False,
    "Lenovo",
    "192.168.1.21",
    120,
    30,
)
NAS = summary(
    "NAS", "00:11:32:c4:7e:92", Category.SERVER, True, False, "Synology", "192.168.1.12", 0, 20
)
PHONE = summary(
    "Pixel", "3a:f1:5c:22:9b:07", Category.PHONE, True, True, None, "192.168.1.30", 0, 1
)
LAB = summary(
    "homelab", "70:85:c2:9e:04:11", Category.SERVER, True, False, None, "192.168.1.10", 0, 10
)
DEVICES = [LAPTOP, NAS, PHONE, LAB]  # fmt: skip


def names(query: BoardQuery) -> list[list[str]]:
    board = build_board(DEVICES, query)
    return [[device.name.value for device in shelf.devices] for shelf in board.shelves]


def titles(query: BoardQuery) -> list[str]:
    return [shelf.title for shelf in build_board(DEVICES, query).shelves]


@pytest.mark.parametrize(
    ("query", "expected"),
    [
        (BoardQuery(), [["homelab", "NAS", "Pixel", "ThinkPad"]]),
        (BoardQuery(order=SortOrder.ASC), [["ThinkPad", "homelab", "NAS", "Pixel"]]),
        (BoardQuery(sort=Sorting.NAME), [["homelab", "NAS", "Pixel", "ThinkPad"]]),
        (BoardQuery(sort=Sorting.NAME, order=SortOrder.DESC), [["ThinkPad", "Pixel", "NAS", "homelab"]]),
        (BoardQuery(sort=Sorting.IP), [["homelab", "NAS", "ThinkPad", "Pixel"]]),
        (BoardQuery(sort=Sorting.IP, order=SortOrder.DESC), [["Pixel", "ThinkPad", "NAS", "homelab"]]),
        (BoardQuery(sort=Sorting.FIRST_SEEN), [["Pixel", "homelab", "NAS", "ThinkPad"]]),
        (BoardQuery(sort=Sorting.FIRST_SEEN, order=SortOrder.ASC), [["ThinkPad", "NAS", "homelab", "Pixel"]]),
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


@pytest.mark.parametrize("order", list(SortOrder))
def test_devices_without_an_ip_sort_last(order: SortOrder) -> None:
    no_ip = replace(LAB, device=replace(LAB.device, ip=None))
    board = build_board([no_ip, NAS, PHONE], BoardQuery(sort=Sorting.IP, order=order))

    assert board.shelves[0].devices[-1] is no_ip


@pytest.mark.parametrize(
    ("grouping", "expected"),
    [
        (Grouping.NONE, ["All devices"]),
        (Grouping.CATEGORY, ["Server", "Computer", "Phone"]),
        (Grouping.VENDOR, ["Lenovo", "Synology", "Private MAC", "Unknown vendor"]),
    ],
)
def test_grouping(grouping: Grouping, expected: list[str]) -> None:
    assert titles(BoardQuery(group=grouping)) == expected


def test_category_shelves_carry_their_category() -> None:
    shelves = build_board(DEVICES, BoardQuery(group=Grouping.CATEGORY)).shelves

    assert [shelf.category for shelf in shelves] == [
        Category.SERVER,
        Category.COMPUTER,
        Category.PHONE,
    ]
    assert shelves[0].online == 2


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


@pytest.mark.parametrize(
    ("query", "applied"),
    [
        (BoardQuery(q="nas"), ()),
        (
            BoardQuery(
                status=StatusFilter.OFFLINE, new=True, category=[Category.SERVER, Category.IOT]
            ),
            (
                AppliedFilter("Offline", "status", "offline"),
                AppliedFilter("New", "new", "true"),
                AppliedFilter("Server", "category", "server"),
                AppliedFilter("Smart home", "category", "iot"),
            ),
        ),
    ],
)
def test_applied_filters(query: BoardQuery, applied: tuple[AppliedFilter, ...]) -> None:
    assert query.applied == applied


@pytest.mark.parametrize(
    ("query", "direction"),
    [
        (BoardQuery(), SortOrder.DESC),
        (BoardQuery(sort=Sorting.NAME), SortOrder.ASC),
        (BoardQuery(sort=Sorting.IP), SortOrder.ASC),
        (BoardQuery(sort=Sorting.FIRST_SEEN), SortOrder.DESC),
        (BoardQuery(sort=Sorting.NAME, order=SortOrder.DESC), SortOrder.DESC),
    ],
)
def test_direction(query: BoardQuery, direction: SortOrder) -> None:
    assert query.direction is direction


@pytest.mark.parametrize(
    ("params", "expected"),
    [
        ({"group": "status", "sort": "smart", "order": "up"}, BoardQuery()),
        ({"group": "vendor", "sort": "ip", "order": "desc"}, BoardQuery(group=Grouping.VENDOR, sort=Sorting.IP, order=SortOrder.DESC)),
    ],
)  # fmt: skip
def test_unknown_presentation_falls_back_to_defaults(
    params: dict[str, str], expected: BoardQuery
) -> None:
    assert BoardQuery.model_validate(params) == expected
