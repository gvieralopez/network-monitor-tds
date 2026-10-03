from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse

from network_monitor_tds.application.plugins import list_plugin_configs
from network_monitor_tds.web.dependencies import ContextDep
from network_monitor_tds.web.templating import templates

router = APIRouter()


@router.get("/settings", response_class=HTMLResponse)
async def settings_page(request: Request, context: ContextDep) -> HTMLResponse:
    configs = await list_plugin_configs(context.unit_of_work())
    plugins = [
        (context.plugins[config.plugin_id], config)
        for config in configs
        if config.plugin_id in context.plugins
    ]
    return templates.TemplateResponse(request, "settings.html", {"plugins": plugins})
