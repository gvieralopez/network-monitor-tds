from collections.abc import Callable, Sequence
from dataclasses import dataclass
from enum import StrEnum
from ipaddress import IPv4Address

from pydantic import BaseModel, ConfigDict

from network_monitor_tds.application.models import DeviceSummary
from network_monitor_tds.domain.devices.models import Category
from network_monitor_tds.web.drawings import CATEGORY_LABELS

PRIVATE_MAC_VENDOR = "Private MAC"
UNKNOWN_VENDOR = "Unknown vendor"
NO_IP = IPv4Address("255.255.255.255")


class StatusFilter(StrEnum):
    ALL = "all"
    ONLINE = "online"
    OFFLINE = "offline"


class Grouping(StrEnum):
    NONE = "none"
    CATEGORY = "category"
    STATUS = "status"
    VENDOR = "vendor"


class Sorting(StrEnum):
    SMART = "smart"
    NAME = "name"
    IP = "ip"
    SEEN = "seen"


GROUPINGS = (
    (Grouping.NONE, "None"),
    (Grouping.CATEGORY, "Category"),
    (Grouping.STATUS, "Status"),
    (Grouping.VENDOR, "Vendor"),
)
SORTINGS = (
    (Sorting.SMART, "New, then online"),
    (Sorting.NAME, "Name"),
    (Sorting.IP, "IP address"),
    (Sorting.SEEN, "Last seen"),
)


class BoardQuery(BaseModel):
    model_config = ConfigDict(frozen=True, extra="ignore")

    q: str = ""
    status: StatusFilter = StatusFilter.ALL
    new: bool = False
    category: list[Category] = []
    group: Grouping = Grouping.NONE
    sort: Sorting = Sorting.SMART

    @property
    def is_filtered(self) -> bool:
        return bool(self.q or self.new or self.category or self.status is not StatusFilter.ALL)


@dataclass(frozen=True, slots=True)
class Shelf:
    title: str
    category: Category | None
    devices: tuple[DeviceSummary, ...]
    spotlight: bool

    @property
    def online(self) -> int:
        return sum(device.online for device in self.devices)


@dataclass(frozen=True, slots=True)
class Board:
    shelves: tuple[Shelf, ...]
    matches: int


def build_board(summaries: Sequence[DeviceSummary], query: BoardQuery) -> Board:
    matching = sorted(
        (summary for summary in summaries if _matches(summary, query)), key=_SORT_KEYS[query.sort]
    )
    return Board(shelves=_shelves(matching, query.group), matches=len(matching))


def vendor_label(summary: DeviceSummary) -> str:
    if summary.device.mac.is_randomized:
        return PRIVATE_MAC_VENDOR
    return summary.vendor or UNKNOWN_VENDOR


def _matches(summary: DeviceSummary, query: BoardQuery) -> bool:
    return (
        _matches_status(summary, query.status)
        and (summary.is_new or not query.new)
        and (not query.category or summary.category.value in query.category)
        and _matches_text(summary, query.q.strip().lower())
    )


def _matches_status(summary: DeviceSummary, status: StatusFilter) -> bool:
    match status:
        case StatusFilter.ONLINE:
            return summary.online
        case StatusFilter.OFFLINE:
            return not summary.online
        case StatusFilter.ALL:
            return True


def _matches_text(summary: DeviceSummary, text: str) -> bool:
    haystack = " ".join(
        (
            summary.name.value,
            str(summary.device.ip or ""),
            str(summary.device.mac),
            summary.vendor or "",
            CATEGORY_LABELS[summary.category.value],
        )
    ).lower()
    return text in haystack


def _shelves(devices: list[DeviceSummary], grouping: Grouping) -> tuple[Shelf, ...]:
    if not devices:
        return ()
    if grouping is Grouping.NONE:
        return (Shelf("All devices", None, tuple(devices), spotlight=False),)
    spotlight = tuple(device for device in devices if device.is_new)
    new_shelf = (
        (Shelf("New on your network", None, spotlight, spotlight=True),)
        if spotlight and grouping is not Grouping.STATUS
        else ()
    )
    return new_shelf + _grouped(devices, grouping)


def _grouped(devices: list[DeviceSummary], grouping: Grouping) -> tuple[Shelf, ...]:
    groups: dict[str, list[DeviceSummary]] = {}
    for device in devices:
        groups.setdefault(_GROUP_KEYS[grouping](device), []).append(device)
    order = _GROUP_ORDERS[grouping]
    return tuple(
        Shelf(
            title=_group_title(key, grouping),
            category=Category(key) if grouping is Grouping.CATEGORY else None,
            devices=tuple(groups[key]),
            spotlight=False,
        )
        for key in sorted(groups, key=order)
    )


def _group_title(key: str, grouping: Grouping) -> str:
    if grouping is Grouping.CATEGORY:
        return CATEGORY_LABELS[Category(key)]
    return key


def _status_group(device: DeviceSummary) -> str:
    if device.is_new:
        return "New"
    return "Online" if device.online else "Offline"


_CATEGORY_ORDER = list(Category)
_STATUS_ORDER = ["New", "Online", "Offline"]

_GROUP_KEYS: dict[Grouping, Callable[[DeviceSummary], str]] = {
    Grouping.CATEGORY: lambda device: device.category.value,
    Grouping.STATUS: _status_group,
    Grouping.VENDOR: vendor_label,
}

_GROUP_ORDERS: dict[Grouping, Callable[[str], tuple[int, str]]] = {
    Grouping.CATEGORY: lambda key: (_CATEGORY_ORDER.index(Category(key)), key),
    Grouping.STATUS: lambda key: (_STATUS_ORDER.index(key), key),
    Grouping.VENDOR: lambda key: (key in (PRIVATE_MAC_VENDOR, UNKNOWN_VENDOR), key.lower()),
}

_SORT_KEYS: dict[Sorting, Callable[[DeviceSummary], tuple[object, ...]]] = {
    Sorting.SMART: lambda d: (not d.is_new, not d.online, d.name.value.lower()),
    Sorting.NAME: lambda d: (d.name.value.lower(),),
    Sorting.IP: lambda d: (d.device.ip or NO_IP,),
    Sorting.SEEN: lambda d: (not d.online, -d.device.last_seen.timestamp(), d.name.value.lower()),
}
