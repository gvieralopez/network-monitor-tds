import json
from typing import Annotated

from fastapi import APIRouter, Form, HTTPException, Request, status
from fastapi.responses import HTMLResponse

from network_monitor_tds.application.errors import UnknownPluginError
from network_monitor_tds.application.plugins import (
    get_plugin_config,
    list_plugin_configs,
    set_plugin_enabled,
    update_plugin_settings,
)
from network_monitor_tds.application.preferences import load_presence_policy, save_presence_policy
from network_monitor_tds.domain.plugins.models import PluginConfig, PluginId
from network_monitor_tds.domain.presence.policy import PresencePolicy
from network_monitor_tds.plugins.host.registry import PluginClass
from network_monitor_tds.web.dependencies import ContextDep
from network_monitor_tds.web.forms import DURATION_HINT, parse_duration, read_settings_form
from network_monitor_tds.web.models import WebContext
from network_monitor_tds.web.pages.settings_views import (
    PresenceView,
    plugin_card,
    policy_view,
    status_view,
    sweep_interval,
)
from network_monitor_tds.web.templating import templates

router = APIRouter(prefix="/settings")

PRESENCE_FIELDS = ("offline_after", "mobile_offline_after")


@router.get("", response_class=HTMLResponse)
async def settings_page(request: Request, context: ContextDep) -> HTMLResponse:
    now = context.clock.now()
    configs = {
        config.plugin_id: config for config in await list_plugin_configs(context.unit_of_work())
    }
    cards = [
        plugin_card(plugin, configs[plugin_id], context.control.status(plugin_id), {}, now)
        for plugin_id, plugin in sorted(context.plugins.items())
        if plugin_id in configs
    ]
    policy = await load_presence_policy(context.unit_of_work())
    return templates.TemplateResponse(
        request,
        "settings.html",
        {"cards": cards, "presence": policy_view(policy, sweep_interval(configs))},
    )


@router.post("/plugins/{plugin_id}/enabled", response_class=HTMLResponse)
async def toggle_plugin(
    request: Request, context: ContextDep, plugin_id: str, enabled: Annotated[bool, Form()] = False
) -> HTMLResponse:
    plugin = _plugin(context, plugin_id)
    config = await set_plugin_enabled(
        context.unit_of_work(), plugin.info.plugin_id, enabled, context.clock.now()
    )
    await context.control.reload(config.plugin_id)
    state = "on" if config.enabled else "off"
    return _card(request, context, plugin, config, {}, f"{plugin.info.name} is {state}")


@router.post("/plugins/{plugin_id}", response_class=HTMLResponse)
async def save_plugin_settings(
    request: Request, context: ContextDep, plugin_id: str
) -> HTMLResponse:
    plugin = _plugin(context, plugin_id)
    config = await get_plugin_config(context.unit_of_work(), plugin.info.plugin_id)
    form = {key: value for key, value in (await request.form()).items() if isinstance(value, str)}
    result = read_settings_form(plugin.settings_model, form, config.settings)
    if result.settings is None:
        return _card(request, context, plugin, config, result.errors, None)
    updated = await update_plugin_settings(
        context.unit_of_work(), config.plugin_id, result.settings, context.clock.now()
    )
    await context.control.reload(updated.plugin_id)
    return _card(request, context, plugin, updated, {}, f"Saved {plugin.info.name} settings")


@router.get("/plugins/{plugin_id}/status", response_class=HTMLResponse)
async def plugin_status(request: Request, context: ContextDep, plugin_id: str) -> HTMLResponse:
    plugin = _plugin(context, plugin_id)
    config = await get_plugin_config(context.unit_of_work(), plugin.info.plugin_id)
    view = status_view(
        config.enabled, context.control.status(config.plugin_id), context.clock.now()
    )
    return templates.TemplateResponse(
        request, "partials/plugin_status.html", {"plugin_id": config.plugin_id, "status": view}
    )


@router.post("/presence", response_class=HTMLResponse)
async def save_presence(
    request: Request,
    context: ContextDep,
    offline_after: Annotated[str, Form()] = "",
    mobile_offline_after: Annotated[str, Form()] = "",
) -> HTMLResponse:
    raw = {"offline_after": offline_after, "mobile_offline_after": mobile_offline_after}
    parsed = {name: parse_duration(raw[name]) for name in PRESENCE_FIELDS}
    errors = {name: DURATION_HINT for name, value in parsed.items() if value is None or not value}
    configs = {
        config.plugin_id: config for config in await list_plugin_configs(context.unit_of_work())
    }
    interval = sweep_interval(configs)
    offline, mobile = parsed["offline_after"], parsed["mobile_offline_after"]
    if errors or offline is None or mobile is None:
        view = PresenceView(offline_after, mobile_offline_after, errors, "")
        return _presence(request, view, None)
    policy = PresencePolicy(offline_after=offline, mobile_offline_after=mobile)
    await save_presence_policy(context.unit_of_work(), policy, context.clock.now())
    view = policy_view(policy, interval)
    return _presence(request, view, "Saved presence settings")


def _plugin(context: WebContext, plugin_id: str) -> PluginClass:
    plugin = context.plugins.get(PluginId(plugin_id))
    if plugin is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(UnknownPluginError(PluginId(plugin_id))))
    return plugin


def _card(
    request: Request,
    context: WebContext,
    plugin: PluginClass,
    config: PluginConfig,
    errors: dict[str, str],
    toast: str | None,
) -> HTMLResponse:
    now = context.clock.now()
    card = plugin_card(plugin, config, context.control.status(config.plugin_id), errors, now)
    response = templates.TemplateResponse(request, "partials/plugin_card.html", {"card": card})
    _trigger(response, toast)
    return response


def _presence(request: Request, view: PresenceView, toast: str | None) -> HTMLResponse:
    response = templates.TemplateResponse(request, "partials/presence.html", {"presence": view})
    _trigger(response, toast)
    return response


def _trigger(response: HTMLResponse, toast: str | None) -> None:
    if toast is not None:
        response.headers["HX-Trigger"] = json.dumps({"toast": toast})
