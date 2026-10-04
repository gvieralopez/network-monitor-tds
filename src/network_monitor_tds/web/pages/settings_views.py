from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import StrEnum

from pydantic import TypeAdapter, ValidationError

from network_monitor_tds.application.models import PluginState, PluginStatus
from network_monitor_tds.domain.plugins.models import JsonValue, PluginConfig, PluginId
from network_monitor_tds.domain.presence.policy import PresencePolicy
from network_monitor_tds.domain.retention.models import (
    MAX_KEEP_DAYS,
    MIN_KEEP_DAYS,
    RetentionPolicy,
)
from network_monitor_tds.plugins.host.registry import PluginClass
from network_monitor_tds.plugins.sdk.models import PluginPurpose
from network_monitor_tds.web.forms import FormField, format_duration, settings_fields
from network_monitor_tds.web.views import ago

SWEEP_PLUGIN = PluginId("arp-sweep")
SWEEPS_BEFORE_OFFLINE = 2
PURPOSE_GROUPS = {
    PluginPurpose.PASSIVE_DISCOVERY: (
        "Passive device finders",
        "Hear devices from the traffic they send anyway. Nothing is sent.",
    ),
    PluginPurpose.ACTIVE_DISCOVERY: (
        "Active device finders",
        "Ask the network who is there, on a schedule.",
    ),
    PluginPurpose.INTEGRATION: (
        "Third-party integrations",
        "Read devices from services you already run.",
    ),
    PluginPurpose.METADATA: (
        "Metadata providers",
        "Add details to devices the other plugins found.",
    ),
    PluginPurpose.DEVELOPMENT: (
        "Developer tools",
        "Simulated devices for trying the app without a real network.",
    ),
}


DURATION = TypeAdapter(timedelta)
RETENTION_HINT = f"Use a whole number of days from {MIN_KEEP_DAYS} to {MAX_KEEP_DAYS}"


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
    purpose: PluginPurpose
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


@dataclass(frozen=True, slots=True)
class RetentionView:
    keep_days: str
    error: str


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
        purpose=plugin.info.purpose,
        enabled=config.enabled,
        status=status_view(config.enabled, status, now),
        fields=settings_fields(plugin.settings_model, config.settings, errors),
        expanded=bool(errors),
    )


def plugin_groups(cards: Iterable[PluginCardView]) -> tuple[PluginGroupView, ...]:
    by_purpose: dict[PluginPurpose, list[PluginCardView]] = {
        purpose: [] for purpose in PURPOSE_GROUPS
    }
    for card in cards:
        by_purpose[card.purpose].append(card)
    return tuple(
        PluginGroupView(*PURPOSE_GROUPS[purpose], tuple(group))
        for purpose, group in by_purpose.items()
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


def retention_view(policy: RetentionPolicy) -> RetentionView:
    return RetentionView(str(policy.keep_days), "")


def parse_retention(text: str) -> RetentionPolicy | None:
    try:
        return RetentionPolicy(keep_days=int(text.strip()))
    except ValueError:
        return None


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
