from dataclasses import replace
from datetime import UTC, timedelta

import pytest

from network_monitor_tds.application.devices import device_detail, list_devices
from network_monitor_tds.application.models import NetworkOverview
from network_monitor_tds.domain.devices.models import Category, DeviceLabels
from network_monitor_tds.domain.network.models import MacAddress
from network_monitor_tds.domain.observations.models import KnownField
from network_monitor_tds.web.drawings import DRAWINGS
from network_monitor_tds.web.models import WebContext
from network_monitor_tds.web.views import (
    ago,
    card_view,
    category_choices,
    chart_view,
    dialog_view,
    drawing_choices,
    hero_view,
    percentage,
)
from tests.conftest import DEMO_INFO, T0, Database

NOW = T0 + timedelta(minutes=5)


@pytest.mark.parametrize(
    ("elapsed", "text"),
    [
        (timedelta(seconds=20), "just now"),
        (timedelta(minutes=12), "12 min ago"),
        (timedelta(hours=3), "3 h ago"),
        (timedelta(days=2), "2 d ago"),
    ],
)
def test_ago(elapsed: timedelta, text: str) -> None:
    assert ago(elapsed) == text


@pytest.mark.parametrize(("ratio", "text"), [(0, "0"), (0.001, "<1"), (0.5, "50"), (1, "100")])
def test_percentage(ratio: float, text: str) -> None:
    assert percentage(ratio) == text


def test_chart_view_scales_to_the_ceiling() -> None:
    chart = chart_view([0, 5, 10], 10)

    assert chart.line == "M0.0,120.0 L500.0,64.0 L1000.0,8.0"
    assert chart.area.startswith("M0,120 L0.0,120.0")
    assert chart.peak == 10
    assert chart.end_top == pytest.approx(8 / 120 * 100)


def test_hero_view() -> None:
    hero = hero_view(NetworkOverview(total=5, online=3, new=1, seen_per_hour=(0,) * 24), NOW)

    assert (hero.online, hero.total, hero.new, hero.offline) == (3, 5, 1, 2)
    assert len(hero.axis) == 3


def test_category_choices_cover_every_category() -> None:
    assert [value for value, _ in category_choices()] == [category.value for category in Category]


def test_drawing_choices_list_every_drawing_in_catalogue_order() -> None:
    assert [choice.name for choice in drawing_choices()] == [d.name for d in DRAWINGS]


def test_drawing_choices_are_searchable_by_label_name_and_category() -> None:
    choice = next(choice for choice in drawing_choices() if choice.name == "console-hybrid-duo")

    assert choice.terms == "hybrid console, two-tone console hybrid duo gaming"
    assert choice.category == Category.GAMING.value


@pytest.mark.anyio
async def test_card_and_drawer_views(
    database: Database, seen_device: MacAddress, web_context: WebContext
) -> None:
    [summary] = await list_devices(database.unit_of_work(), NOW)
    card = card_view(summary, NOW)

    assert (card.name, card.category, card.icon, card.color) == (
        "esp-31f5e", "Smart home", "chip", "iot"
    )  # fmt: skip
    assert (card.status, card.seen, card.is_new) == ("Online", "now", True)

    offline = card_view(replace(summary, online=False), T0 + timedelta(hours=2))
    assert (offline.status, offline.seen) == ("2 h ago", "seen 2 h ago")

    detail = await device_detail(database.unit_of_work(), seen_device, NOW, UTC)
    dialog = dialog_view(detail, web_context.plugin_names, NOW)
    assert dialog.first_found_by == DEMO_INFO.name
    assert dialog.discoveries[0].details == "dhcp hostname: esp-31f5e"
    assert (dialog.detected_name, dialog.name_origin, dialog.detected_category) == (
        "esp-31f5e", "DHCP", "Smart home"
    )  # fmt: skip
    assert (dialog.labels_name, dialog.labels_category, dialog.labels_icon) == ("", "", "")
    assert dialog.automatic_icon == "chip"
    assert len(dialog.rows) == 14


@pytest.mark.anyio
async def test_dialog_keeps_detected_values_next_to_labels(
    database: Database, seen_device: MacAddress, web_context: WebContext
) -> None:
    async with database.unit_of_work() as uow:
        device = await uow.devices.get(seen_device)
        assert device is not None
        labels = DeviceLabels("Garden sensor", Category.CAMERA, "camera")
        await uow.devices.save(device.relabel(labels))
        await uow.facts.save(seen_device, {})
        await uow.commit()

    detail = await device_detail(database.unit_of_work(), seen_device, NOW, UTC)
    dialog = dialog_view(detail, {}, NOW)

    assert dialog.card.name == "Garden sensor"
    assert dialog.detected_name == "esp-31f5e"
    assert (dialog.detected_category, dialog.detected_category_value) == ("Smart home", "iot")
    assert (dialog.labels_category, dialog.labels_icon) == ("camera", "camera")
    assert dialog.automatic_icon == "camera"
    assert dialog.first_found_by == "demo"
    assert KnownField.DHCP_HOSTNAME in detail.facts
