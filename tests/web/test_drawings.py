import re
import xml.etree.ElementTree as ET

import pytest

from network_monitor_tds.domain.devices.models import Category
from network_monitor_tds.web.drawings import (
    CATEGORY_COLORS,
    CATEGORY_DRAWINGS,
    CATEGORY_LABELS,
    DRAWING_NAMES,
    DRAWINGS,
    Drawing,
)
from network_monitor_tds.web.templating import TEMPLATES_DIR

SVG = "{http://www.w3.org/2000/svg}"
SPRITE = ET.fromstring((TEMPLATES_DIR / "drawings.svg").read_text())
SYMBOLS = {symbol.get("id"): symbol for symbol in SPRITE.iter(f"{SVG}symbol")}
SHARED_IDS = {
    element.get("id")
    for element in SPRITE.iterfind(f"{SVG}defs/*")
    if element.tag != f"{SVG}symbol"
}
URL_REFERENCE = re.compile(r"url\(#([\w-]+)\)")
SAFE_HALF_WIDTH = 84
ORIGINAL_ICON_NAMES = (
    "router", "wifi", "server", "disk", "laptop", "desktop", "phone", "tablet", "watch", "tv",
    "speaker", "gamepad", "bulb", "plug", "vacuum", "camera", "printer", "chip", "question",
)  # fmt: skip


def test_names_are_unique() -> None:
    assert len(DRAWING_NAMES) == len(DRAWINGS)


def test_every_drawing_has_a_symbol_and_every_symbol_a_drawing() -> None:
    assert set(SYMBOLS) == {f"dv-{name}" for name in DRAWING_NAMES}


@pytest.mark.parametrize("name", sorted(DRAWING_NAMES))
def test_symbol_follows_the_canvas_rules(name: str) -> None:
    symbol = SYMBOLS[f"dv-{name}"]
    inner = list(symbol.iter())[1:]

    assert symbol.get("viewBox") == "0 0 200 140"
    assert [element.get("id") for element in inner if element.get("id")] == []
    references = {
        ref for element in inner for ref in URL_REFERENCE.findall(element.get("fill", ""))
    }
    assert references <= SHARED_IDS


@pytest.mark.parametrize("drawing", DRAWINGS, ids=lambda drawing: drawing.name)
def test_footprint_fits_the_safe_area(drawing: Drawing) -> None:
    assert 0 < drawing.footprint <= SAFE_HALF_WIDTH


@pytest.mark.parametrize("name", ORIGINAL_ICON_NAMES)
def test_original_icon_names_still_exist(name: str) -> None:
    assert name in DRAWING_NAMES


@pytest.mark.parametrize("category", list(Category))
def test_every_category_has_a_label_colour_and_default_listed_under_it(category: Category) -> None:
    default = next(drawing for drawing in DRAWINGS if drawing.name == CATEGORY_DRAWINGS[category])

    assert default.category is category
    assert category in CATEGORY_LABELS
    assert category in CATEGORY_COLORS
