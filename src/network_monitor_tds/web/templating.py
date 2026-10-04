from pathlib import Path

from fastapi import Request
from fastapi.templating import Jinja2Templates

from network_monitor_tds import __version__
from network_monitor_tds.web.icons import ICONS
from network_monitor_tds.web.views import category_choices

TEMPLATES_DIR = Path(__file__).parent / "templates"
THEME_COOKIE = "nmtds_theme"
THEMES = (("auto", "Auto"), ("light", "Light"), ("dark", "Dark"))


def theme_of(request: Request) -> str:
    chosen = request.cookies.get(THEME_COOKIE, "auto")
    return chosen if chosen in dict(THEMES) else "auto"


templates = Jinja2Templates(directory=TEMPLATES_DIR)
templates.env.globals.update(
    version=__version__,
    icon_paths=ICONS,
    category_choices=category_choices(),
    theme_of=theme_of,
    themes=THEMES,
    theme_cookie=THEME_COOKIE,
)
