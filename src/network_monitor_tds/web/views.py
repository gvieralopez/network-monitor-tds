from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import datetime, timedelta

from network_monitor_tds.application.models import DeviceDetail, DeviceSummary, NetworkOverview
from network_monitor_tds.domain.devices.classification import classify
from network_monitor_tds.domain.devices.identity import resolve_name
from network_monitor_tds.domain.devices.models import NO_LABELS, Category, Fallback, Origin
from network_monitor_tds.domain.observations.models import Fact, KnownField
from network_monitor_tds.domain.plugins.models import PluginId
from network_monitor_tds.plugins.sdk.models import PluginInfo
from network_monitor_tds.web.art import Artwork, artwork
from network_monitor_tds.web.icons import CATEGORY_COLORS, CATEGORY_ICONS, CATEGORY_LABELS
from network_monitor_tds.web.pages.board import vendor_label

CHART_WIDTH = 1000
CHART_HEIGHT = 120
CHART_TOP = 8
MINUTES_PER_HOUR = 60
MINUTES_PER_DAY = 24 * MINUTES_PER_HOUR
SMALLEST_PERCENTAGE = 0.005

ORIGIN_LABELS: dict[Origin, str] = {
    KnownField.LEASE_HOSTNAME: "DHCP lease",
    KnownField.DHCP_HOSTNAME: "DHCP",
    KnownField.MDNS_NAME: "mDNS",
    KnownField.UPNP_FRIENDLY_NAME: "UPnP",
    KnownField.VENDOR: "vendor",
    Fallback.MAC_ADDRESS: "MAC address",
}


@dataclass(frozen=True, slots=True)
class CardView:
    mac: str
    name: str
    category: str
    color: str
    icon: str
    vendor: str
    ip: str
    online: bool
    is_new: bool
    status: str
    seen: str
    hours_online: int
    strip: tuple[bool, ...]
    art: Artwork


@dataclass(frozen=True, slots=True)
class ChartView:
    line: str
    area: str
    end_top: float
    series: tuple[int, ...]
    peak: int
    width: int
    height: int


@dataclass(frozen=True, slots=True)
class HeroView:
    online: int
    total: int
    new: int
    offline: int
    chart: ChartView
    axis: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class DiscoveryView:
    name: str
    first: bool
    details: str


@dataclass(frozen=True, slots=True)
class HeatRowView:
    label: str
    hours: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class DrawerView:
    card: CardView
    first_seen: str
    first_found_by: str
    discoveries: tuple[DiscoveryView, ...]
    rows: tuple[HeatRowView, ...]
    uptime: str
    detected_name: str
    name_origin: str
    detected_category: str
    labels_name: str
    labels_category: str
    labels_icon: str


def card_view(summary: DeviceSummary, now: datetime) -> CardView:
    device = summary.device
    category = summary.category.value
    return CardView(
        mac=str(device.mac),
        name=summary.name.value,
        category=CATEGORY_LABELS[category],
        color=CATEGORY_COLORS[category],
        icon=device.labels.icon or CATEGORY_ICONS[category],
        vendor=vendor_label(summary),
        ip=str(device.ip or "No IP"),
        online=summary.online,
        is_new=summary.is_new,
        status="Online" if summary.online else ago(now - device.last_seen),
        seen="now" if summary.online else f"seen {ago(now - device.last_seen)}",
        hours_online=summary.hours_online,
        strip=summary.last_24_hours,
        art=artwork(device.mac),
    )


def ago(elapsed: timedelta) -> str:
    minutes = elapsed.total_seconds() / 60
    if minutes < 1:
        return "just now"
    if minutes < MINUTES_PER_HOUR:
        return f"{minutes:.0f} min ago"
    if minutes < MINUTES_PER_DAY:
        return f"{minutes / MINUTES_PER_HOUR:.0f} h ago"
    return f"{minutes / MINUTES_PER_DAY:.0f} d ago"


def hero_view(overview: NetworkOverview, now: datetime) -> HeroView:
    first_hour = now.replace(minute=0, second=0, microsecond=0) - timedelta(hours=23)
    return HeroView(
        online=overview.online,
        total=overview.total,
        new=overview.new,
        offline=overview.total - overview.online,
        chart=chart_view(overview.seen_per_hour, max(overview.total, 1)),
        axis=tuple(
            (first_hour + timedelta(hours=offset)).astimezone().strftime("%H:00")
            for offset in (0, 8, 16)
        ),
    )


def chart_view(series: Sequence[int], ceiling: int) -> ChartView:
    top = max(ceiling, *series)
    step = CHART_WIDTH / max(len(series) - 1, 1)
    points = [
        f"{index * step:.1f},{CHART_TOP + (1 - value / top) * (CHART_HEIGHT - CHART_TOP):.1f}"
        for index, value in enumerate(series)
    ]
    end_y = CHART_TOP + (1 - series[-1] / top) * (CHART_HEIGHT - CHART_TOP)
    return ChartView(
        line="M" + " L".join(points),
        area=f"M0,{CHART_HEIGHT} L{' L'.join(points)} L{CHART_WIDTH},{CHART_HEIGHT} Z",
        end_top=end_y / CHART_HEIGHT * 100,
        series=tuple(series),
        peak=max(series),
        width=CHART_WIDTH,
        height=CHART_HEIGHT,
    )


def drawer_view(
    detail: DeviceDetail, plugins: Mapping[PluginId, PluginInfo], now: datetime
) -> DrawerView:
    summary, device = detail.summary, detail.summary.device
    card = card_view(summary, now)
    detected_name = resolve_name(device.mac, NO_LABELS, detail.facts)
    discoveries = tuple(
        DiscoveryView(
            name=_plugin_name(detection.source, plugins),
            first=index == 0,
            details=_details(detection.source, detail.facts),
        )
        for index, detection in enumerate(detail.detections)
    )
    return DrawerView(
        card=card,
        first_seen=device.first_seen.astimezone().strftime("%-d %b, %H:%M"),
        first_found_by=discoveries[0].name if discoveries else "Unknown",
        discoveries=discoveries,
        rows=tuple(
            HeatRowView(
                label=day.day.strftime("%a %-d"), hours=tuple(state.value for state in day.hours)
            )
            for day in detail.days
        ),
        uptime=percentage(detail.uptime_last_7_days),
        detected_name=detected_name.value,
        name_origin=ORIGIN_LABELS.get(detected_name.origin, detected_name.origin.value),
        detected_category=CATEGORY_LABELS[classify(detail.facts).value],
        labels_name=device.labels.name or "",
        labels_category=device.labels.category.value if device.labels.category else "",
        labels_icon=device.labels.icon or "",
    )


def percentage(ratio: float) -> str:
    if 0 < ratio < SMALLEST_PERCENTAGE:
        return "<1"
    return f"{ratio * 100:.0f}"


def category_choices() -> tuple[tuple[str, str], ...]:
    return tuple((category.value, CATEGORY_LABELS[category]) for category in Category)


def _plugin_name(plugin_id: PluginId, plugins: Mapping[PluginId, PluginInfo]) -> str:
    info = plugins.get(plugin_id)
    return info.name if info is not None else plugin_id


def _details(plugin_id: PluginId, facts: Mapping[str, Fact]) -> str:
    return "\n".join(
        f"{fact.name.replace('_', ' ')}: {fact.value}"
        for fact in facts.values()
        if fact.source == plugin_id
    )
