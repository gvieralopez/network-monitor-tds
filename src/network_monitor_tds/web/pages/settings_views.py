from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import StrEnum

from pydantic import TypeAdapter, ValidationError

from network_monitor_tds.application.models import PluginState, PluginStatus
from network_monitor_tds.domain.plugins.models import JsonValue, PluginConfig, PluginId
from network_monitor_tds.domain.presence.policy import PresencePolicy
from network_monitor_tds.plugins.host.registry import PluginClass
from network_monitor_tds.plugins.sdk.models import PluginKind
from network_monitor_tds.web.forms import FormField, format_duration, settings_fields
from network_monitor_tds.web.views import ago

SWEEP_PLUGIN = PluginId("arp-sweep")
SWEEPS_BEFORE_OFFLINE = 2
KIND_GROUPS = {
    PluginKind.LISTENER: (
        "Listen passively",
        "Hear devices as they talk on the network. Nothing is sent.",
    ),
    PluginKind.SCHEDULED: (
        "Check on a schedule",
        "Scan the network or ask other services for devices every few minutes.",
    ),
    PluginKind.ENRICHMENT: ("Enrich devices", "Add details to devices the other plugins found."),
}


DURATION = TypeAdapter(timedelta)


class Tone(StrEnum):
    GOOD = "good"
    BAD = "bad"
    QUIET = "quiet"


@dataclass(frozen=True, slots=True)
class StatusView:
    text: str
    tone: Tone


@dataclass(frozen=True, slots=True)
class PluginCardView:
    plugin_id: str
    name: str
    description: str
    kind: PluginKind
    enabled: bool
    status: StatusView
    fields: tuple[FormField, ...]
    expanded: bool


@dataclass(frozen=True, slots=True)
class PluginGroupView:
    title: str
    lede: str
    cards: tuple[PluginCardView, ...]


@dataclass(frozen=True, slots=True)
class PresenceView:
    offline_after: str
    mobile_offline_after: str
    errors: Mapping[str, str]
    warning: str


def plugin_card(
    plugin: PluginClass,
    config: PluginConfig,
    status: PluginStatus,
    errors: Mapping[str, str],
    now: datetime,
) -> PluginCardView:
    return PluginCardView(
        plugin_id=config.plugin_id,
        name=plugin.info.name,
        description=plugin.info.description,
        kind=plugin.kind,
        enabled=config.enabled,
        status=status_view(config.enabled, status, now),
        fields=settings_fields(plugin.settings_model, config.settings, errors),
        expanded=bool(errors),
    )


def plugin_groups(cards: Iterable[PluginCardView]) -> tuple[PluginGroupView, ...]:
    by_kind: dict[PluginKind, list[PluginCardView]] = {kind: [] for kind in KIND_GROUPS}
    for card in cards:
        by_kind[card.kind].append(card)
    return tuple(
        PluginGroupView(*KIND_GROUPS[kind], tuple(group))
        for kind, group in by_kind.items()
        if group
    )


def status_view(enabled: bool, status: PluginStatus, now: datetime) -> StatusView:
    if not enabled:
        return StatusView("Off", Tone.QUIET)
    match status.state:
        case PluginState.FAILING:
            return StatusView(f"Error: {status.last_error}", Tone.BAD)
        case PluginState.RUNNING if status.last_success is not None:
            return StatusView(f"Working · last success {ago(now - status.last_success)}", Tone.GOOD)
        case PluginState.RUNNING:
            return StatusView("Running", Tone.GOOD)
        case _:
            return StatusView("Not running", Tone.QUIET)


def policy_view(policy: PresencePolicy, sweep_interval: timedelta | None) -> PresenceView:
    return PresenceView(
        format_duration(policy.offline_after),
        format_duration(policy.mobile_offline_after),
        {},
        sweep_warning(policy, sweep_interval),
    )


def sweep_warning(policy: PresencePolicy, sweep_interval: timedelta | None) -> str:
    if sweep_interval is None:
        return ""
    shortest = min(policy.offline_after, policy.mobile_offline_after)
    if shortest >= sweep_interval * SWEEPS_BEFORE_OFFLINE:
        return ""
    return (
        f"The ARP sweep runs every {format_duration(sweep_interval)}. Thresholds shorter than "
        f"{format_duration(sweep_interval * SWEEPS_BEFORE_OFFLINE)} will make quiet devices "
        "flicker between online and offline."
    )


def sweep_interval(configs: Mapping[PluginId, PluginConfig]) -> timedelta | None:
    config = configs.get(SWEEP_PLUGIN)
    if config is None or not config.enabled:
        return None
    return _interval(config.settings)


def _interval(settings: Mapping[str, JsonValue]) -> timedelta | None:
    try:
        return DURATION.validate_python(settings.get("interval"))
    except ValidationError:
        return None
