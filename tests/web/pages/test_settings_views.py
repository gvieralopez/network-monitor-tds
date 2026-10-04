from datetime import timedelta

import pytest

from network_monitor_tds.application.models import PluginState, PluginStatus
from network_monitor_tds.domain.plugins.models import PluginConfig, PluginId
from network_monitor_tds.domain.presence.policy import DEFAULT_POLICY, PresencePolicy
from network_monitor_tds.domain.retention.models import RetentionPolicy
from network_monitor_tds.plugins.builtin.capture.errors import CapturePermissionError
from network_monitor_tds.plugins.builtin.technitium.plugin import TechnitiumPlugin
from network_monitor_tds.plugins.sdk.models import PluginPurpose
from network_monitor_tds.web.pages.settings_views import (
    DOCS_URL,
    PluginCardView,
    StatusView,
    Tone,
    parse_retention,
    plugin_groups,
    policy_view,
    setup_hint,
    status_view,
    sweep_interval,
    sweep_warning,
)
from tests.conftest import T0

NOW = T0 + timedelta(minutes=3)
SWEEP = PluginId("arp-sweep")


@pytest.mark.parametrize(
    ("enabled", "status", "view"),
    [
        (False, PluginStatus(PluginState.RUNNING, None, None), StatusView("Off", Tone.QUIET, "")),
        (True, PluginStatus(PluginState.FAILING, T0, "no access"), StatusView("no access", Tone.BAD, "")),
        (
            True,
            PluginStatus(PluginState.FAILING, T0, str(CapturePermissionError())),
            StatusView("Needs packet-capture permission", Tone.BAD, f"{DOCS_URL}/capture-permissions.md"),
        ),
        (True, PluginStatus(PluginState.RUNNING, T0, None), StatusView("Working · last success 3 min ago", Tone.GOOD, "")),
        (True, PluginStatus(PluginState.RUNNING, None, None), StatusView("Running", Tone.GOOD, "")),
        (True, PluginStatus(PluginState.STOPPED, None, None), StatusView("Not running", Tone.QUIET, "")),
    ],
)  # fmt: skip
def test_status_view(enabled: bool, status: PluginStatus, view: StatusView) -> None:
    assert status_view(enabled, status, NOW) == view


def config(enabled: bool, interval: str) -> dict[PluginId, PluginConfig]:
    return {SWEEP: PluginConfig(SWEEP, enabled, {"interval": interval}, T0)}


@pytest.mark.parametrize(
    ("configs", "interval"),
    [
        (config(True, "PT5M"), timedelta(minutes=5)),
        (config(False, "PT5M"), None),
        (config(True, "garbage"), None),
        ({}, None),
    ],
)
def test_sweep_interval(configs: dict[PluginId, PluginConfig], interval: timedelta | None) -> None:
    assert sweep_interval(configs) == interval


@pytest.mark.parametrize(
    ("policy", "interval", "warns"),
    [
        (DEFAULT_POLICY, timedelta(minutes=5), False),
        (DEFAULT_POLICY, None, False),
        (PresencePolicy(timedelta(minutes=3), timedelta(minutes=20)), timedelta(minutes=5), True),
    ],
)
def test_sweep_warning(policy: PresencePolicy, interval: timedelta | None, warns: bool) -> None:
    assert bool(sweep_warning(policy, interval)) is warns


def test_policy_view() -> None:
    view = policy_view(DEFAULT_POLICY, timedelta(minutes=5))

    assert (view.offline_after, view.mobile_offline_after, view.warning) == ("10m", "15m", "")


@pytest.mark.parametrize(
    ("purposes", "titles"),
    [
        ([], []),
        (
            [PluginPurpose.DEVELOPMENT, PluginPurpose.PASSIVE_DISCOVERY],
            [("Passive device finders", 1), ("Developer tools", 1)],
        ),
        (
            [PluginPurpose.INTEGRATION, PluginPurpose.METADATA, PluginPurpose.ACTIVE_DISCOVERY],
            [("Active device finders", 1), ("Third-party integrations", 1), ("Metadata providers", 1)],
        ),
        ([PluginPurpose.PASSIVE_DISCOVERY] * 2, [("Passive device finders", 2)]),
    ],
)  # fmt: skip
def test_plugin_groups(purposes: list[PluginPurpose], titles: list[tuple[str, int]]) -> None:
    cards = [_card(f"plugin-{index}", purpose) for index, purpose in enumerate(purposes)]

    groups = plugin_groups(cards)

    assert [(group.title, len(group.cards)) for group in groups] == titles


def _card(plugin_id: str, purpose: PluginPurpose) -> PluginCardView:
    return PluginCardView(
        plugin_id, plugin_id, "", purpose, True, StatusView("Off", Tone.QUIET, ""), "", (), False
    )


@pytest.mark.parametrize(
    ("text", "policy"),
    [("90", RetentionPolicy(90)), (" 14 ", RetentionPolicy(14)), ("13", None), ("-20", None), ("2w", None), ("", None)],
)  # fmt: skip
def test_parse_retention(text: str, policy: RetentionPolicy | None) -> None:
    assert parse_retention(text) == policy


@pytest.mark.parametrize(
    ("enabled", "settings", "hint"),
    [
        (False, {}, "Fill in “Server address” and “API token”, then switch it on."),
        (False, {"url": "http://dns:5380"}, "Fill in “API token”, then switch it on."),
        (False, {"url": "http://dns:5380", "token": "t"}, ""),
        (True, {}, ""),
    ],
)
def test_setup_hint(enabled: bool, settings: dict[str, str], hint: str) -> None:
    config = PluginConfig(PluginId("technitium"), enabled, settings, T0)

    assert setup_hint(TechnitiumPlugin, config) == hint
