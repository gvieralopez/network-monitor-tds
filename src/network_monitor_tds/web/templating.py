from pathlib import Path

from fastapi.templating import Jinja2Templates

from network_monitor_tds import __version__
from network_monitor_tds.web.icons import ICONS
from network_monitor_tds.web.views import category_choices

TEMPLATES_DIR = Path(__file__).parent / "templates"

templates = Jinja2Templates(directory=TEMPLATES_DIR)
templates.env.globals.update(
    version=__version__, icon_paths=ICONS, category_choices=category_choices()
)
