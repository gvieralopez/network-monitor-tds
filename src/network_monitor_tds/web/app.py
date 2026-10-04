from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import PlainTextResponse
from fastapi.staticfiles import StaticFiles

from network_monitor_tds import __version__
from network_monitor_tds.application.errors import DeviceNotFoundError
from network_monitor_tds.web import sse
from network_monitor_tds.web.api.v1 import devices as api_devices
from network_monitor_tds.web.models import WebContext
from network_monitor_tds.web.pages import devices, settings

STATIC_DIR = Path(__file__).parent / "static"


def create_app(context: WebContext) -> FastAPI:
    app = FastAPI(title="Network Monitor TDS", version=__version__, docs_url=None, redoc_url=None)
    app.state.context = context
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
    app.include_router(devices.router)
    app.include_router(settings.router)
    app.include_router(sse.router)
    app.include_router(api_devices.router)
    app.add_exception_handler(DeviceNotFoundError, _not_found)
    return app


async def _not_found(_request: Request, error: Exception) -> PlainTextResponse:
    return PlainTextResponse(str(error), status_code=404)
