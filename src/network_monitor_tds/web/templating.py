from pathlib import Path

from fastapi import Request
from fastapi.templating import Jinja2Templates

from network_monitor_tds import __version__
from network_monitor_tds.web.drawings import CATEGORY_COLORS, DRAWINGS
from network_monitor_tds.web.pages.board import GROUPINGS, SORTINGS, Grouping, Sorting
from network_monitor_tds.web.views import category_choices, drawing_choices

TEMPLATES_DIR = Path(__file__).parent / "templates"
THEME_COOKIE = "nmtds_theme"
THEMES = (("auto", "Auto"), ("light", "Light"), ("dark", "Dark"))
CARD_STYLE_COOKIE = "nmtds_cards"
CARD_STYLES = (("artwork", "Artwork"), ("studio", "Studio"))
GROUPING_COOKIE = "nmtds_group"
SORTING_COOKIE = "nmtds_sort"


def theme_of(request: Request) -> str:
    return _chosen(request, THEME_COOKIE, THEMES, "auto")


def card_style_of(request: Request) -> str:
    return _chosen(request, CARD_STYLE_COOKIE, CARD_STYLES, "artwork")


def grouping_of(request: Request) -> Grouping:
    return Grouping(_chosen(request, GROUPING_COOKIE, GROUPINGS, Grouping.NONE))


def sorting_of(request: Request) -> Sorting:
    return Sorting(_chosen(request, SORTING_COOKIE, SORTINGS, Sorting.SEEN))


templates = Jinja2Templates(directory=TEMPLATES_DIR)
templates.env.globals.update(
    version=__version__,
    drawing_choices=drawing_choices(),
    category_colors=CATEGORY_COLORS,
    category_choices=category_choices(),
    theme_of=theme_of,
    themes=THEMES,
    theme_cookie=THEME_COOKIE,
    card_style_of=card_style_of,
    card_styles=CARD_STYLES,
    card_style_cookie=CARD_STYLE_COOKIE,
    grouping_of=grouping_of,
    groupings=GROUPINGS,
    grouping_cookie=GROUPING_COOKIE,
    sorting_of=sorting_of,
    sortings=SORTINGS,
    sorting_cookie=SORTING_COOKIE,
    drawing_footprints={drawing.name: drawing.footprint for drawing in DRAWINGS},
)


def _chosen(
    request: Request, cookie: str, choices: tuple[tuple[str, str], ...], default: str
) -> str:
    chosen = request.cookies.get(cookie, default)
    return chosen if chosen in dict(choices) else default
