import math
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, ValidationInfo, field_validator

from network_monitor_tds.application.models import DeviceSummary
from network_monitor_tds.domain.devices.models import Category
from network_monitor_tds.web.drawings import CATEGORY_LABELS

PRIVATE_MAC_VENDOR = "Private MAC"
UNKNOWN_VENDOR = "Unknown vendor"


class StatusFilter(StrEnum):
    ALL = "all"
    ONLINE = "online"
    OFFLINE = "offline"


class Grouping(StrEnum):
    NONE = "none"
    CATEGORY = "category"
    VENDOR = "vendor"


class Sorting(StrEnum):
    SEEN = "seen"
    NAME = "name"
    IP = "ip"
    FIRST_SEEN = "first-seen"


class SortOrder(StrEnum):
    ASC = "asc"
    DESC = "desc"


GROUPINGS = ((Grouping.NONE, "None"), (Grouping.CATEGORY, "Category"), (Grouping.VENDOR, "Vendor"))
SORTINGS = (
    (Sorting.SEEN, "Last seen"),
    (Sorting.NAME, "Name"),
    (Sorting.IP, "IP address"),
    (Sorting.FIRST_SEEN, "First seen"),
)
NATURAL_ORDERS = {
    Sorting.SEEN: SortOrder.DESC,
    Sorting.NAME: SortOrder.ASC,
    Sorting.IP: SortOrder.ASC,
    Sorting.FIRST_SEEN: SortOrder.DESC,
}
ORDER_LABELS = {
    Sorting.SEEN: {SortOrder.ASC: "Longest ago first", SortOrder.DESC: "Most recent first"},
    Sorting.NAME: {SortOrder.ASC: "A to Z", SortOrder.DESC: "Z to A"},
    Sorting.IP: {SortOrder.ASC: "Lowest first", SortOrder.DESC: "Highest first"},
    Sorting.FIRST_SEEN: {SortOrder.ASC: "Oldest first", SortOrder.DESC: "Newest first"},
}


class BoardQuery(BaseModel):
    model_config = ConfigDict(frozen=True, extra="ignore")

    q: str = ""
    status: StatusFilter = StatusFilter.ALL
    new: bool = False
    category: list[Category] = []
    group: Grouping = Grouping.NONE
    sort: Sorting = Sorting.SEEN
    order: SortOrder | None = None

    @field_validator("group", "sort", "order", mode="before")
    @classmethod
    def _ignore_unknown(cls, value: object, info: ValidationInfo) -> object:
        name = str(info.field_name)
        known = {str(choice) for choice in _CHOICES[name]}
        return value if value in known else cls.model_fields[name].default

    @property
    def is_filtered(self) -> bool:
        return bool(self.q or self.new or self.category or self.status is not StatusFilter.ALL)

    @property
    def direction(self) -> SortOrder:
        return self.order or NATURAL_ORDERS[self.sort]

    @property
    def applied(self) -> tuple[AppliedFilter, ...]:
        status = (
            (AppliedFilter(_STATUS_LABELS[self.status], "status", self.status.value),)
            if self.status is not StatusFilter.ALL
            else ()
        )
        new = (AppliedFilter("New", "new", "true"),) if self.new else ()
        categories = tuple(
            AppliedFilter(CATEGORY_LABELS[category], "category", category.value)
            for category in self.category
        )
        return status + new + categories


@dataclass(frozen=True, slots=True)
class AppliedFilter:
    label: str
    field: str
    value: str


@dataclass(frozen=True, slots=True)
class Shelf:
    title: str
    category: Category | None
    devices: tuple[DeviceSummary, ...]

    @property
    def online(self) -> int:
        return sum(device.online for device in self.devices)


@dataclass(frozen=True, slots=True)
class Board:
    shelves: tuple[Shelf, ...]
    matches: int


def build_board(summaries: Sequence[DeviceSummary], query: BoardQuery) -> Board:
    matching = _sorted(
        [summary for summary in summaries if _matches(summary, query)], query.sort, query.direction
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


def _sorted(devices: list[DeviceSummary], sort: Sorting, order: SortOrder) -> list[DeviceSummary]:
    by_name = sorted(devices, key=lambda device: device.name.value.lower())
    key = _SORT_KEYS[sort]
    ranked = [(rank, device) for device in by_name if (rank := key(device)) is not None]
    ranked.sort(key=lambda pair: pair[0], reverse=order is SortOrder.DESC)
    unranked = [device for device in by_name if key(device) is None]
    return [device for _, device in ranked] + unranked


def _shelves(devices: list[DeviceSummary], grouping: Grouping) -> tuple[Shelf, ...]:
    if not devices:
        return ()
    if grouping is Grouping.NONE:
        return (Shelf("All devices", None, tuple(devices)),)
    return _grouped(devices, grouping)


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
        )
        for key in sorted(groups, key=order)
    )


def _group_title(key: str, grouping: Grouping) -> str:
    if grouping is Grouping.CATEGORY:
        return CATEGORY_LABELS[Category(key)]
    return key


_STATUS_LABELS = {StatusFilter.ONLINE: "Online", StatusFilter.OFFLINE: "Offline"}
_CHOICES: dict[str, type[StrEnum]] = {"group": Grouping, "sort": Sorting, "order": SortOrder}
_CATEGORY_ORDER = list(Category)

_GROUP_KEYS: dict[Grouping, Callable[[DeviceSummary], str]] = {
    Grouping.CATEGORY: lambda device: device.category.value,
    Grouping.VENDOR: vendor_label,
}

_GROUP_ORDERS: dict[Grouping, Callable[[str], tuple[int, str]]] = {
    Grouping.CATEGORY: lambda key: (_CATEGORY_ORDER.index(Category(key)), key),
    Grouping.VENDOR: lambda key: (key in (PRIVATE_MAC_VENDOR, UNKNOWN_VENDOR), key.lower()),
}

_SORT_KEYS: dict[Sorting, Callable[[DeviceSummary], tuple[object, ...] | None]] = {
    Sorting.SEEN: lambda d: (math.inf if d.online else d.device.last_seen.timestamp(),),
    Sorting.NAME: lambda d: (d.name.value.lower(),),
    Sorting.IP: lambda d: (d.device.ip,) if d.device.ip else None,
    Sorting.FIRST_SEEN: lambda d: (d.device.first_seen.timestamp(),),
}
