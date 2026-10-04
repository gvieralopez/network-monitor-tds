import json
from typing import Annotated

from fastapi import APIRouter, Form, Query, Request
from fastapi.responses import HTMLResponse

from network_monitor_tds.application.devices import (
    acknowledge_device,
    device_detail,
    forget_device,
    list_devices,
    network_overview,
    relabel_device,
)
from network_monitor_tds.domain.network.models import MacAddress
from network_monitor_tds.web.dependencies import ContextDep, MacDep
from network_monitor_tds.web.icons import CATEGORY_COLORS, CATEGORY_LABELS
from network_monitor_tds.web.models import WebContext
from network_monitor_tds.web.pages.board import BoardQuery, build_board
from network_monitor_tds.web.pages.schemas import LabelsForm
from network_monitor_tds.web.templating import templates
from network_monitor_tds.web.views import card_view, drawer_view, hero_view

router = APIRouter()


@router.get("/", response_class=HTMLResponse)
async def devices_page(
    request: Request, context: ContextDep, query: Annotated[BoardQuery, Query()]
) -> HTMLResponse:
    now = context.clock.now()
    summaries = await list_devices(context.unit_of_work(), now)
    board = build_board(summaries, query)
    counts = {category: 0 for category in CATEGORY_LABELS}
    for summary in summaries:
        counts[summary.category.value] += 1
    return templates.TemplateResponse(
        request,
        "devices.html",
        {
            "hero": hero_view(network_overview(summaries), now),
            "board": board,
            "cards": {str(summary.device.mac): card_view(summary, now) for summary in summaries},
            "query": query,
            "category_counts": {category: count for category, count in counts.items() if count},
            "category_labels": CATEGORY_LABELS,
            "category_colors": CATEGORY_COLORS,
            "new_count": sum(summary.is_new for summary in summaries),
        },
    )


@router.get("/devices/{mac}", response_class=HTMLResponse)
async def device_drawer(request: Request, context: ContextDep, mac: MacDep) -> HTMLResponse:
    return await _drawer(request, context, mac, {})


@router.post("/devices/{mac}/labels", response_class=HTMLResponse)
async def save_labels(
    request: Request, context: ContextDep, mac: MacDep, form: Annotated[LabelsForm, Form()]
) -> HTMLResponse:
    await relabel_device(context.unit_of_work(), mac, form.to_labels())
    return await _drawer(request, context, mac, {"devices-changed": None, "toast": "Saved"})


@router.post("/devices/{mac}/acknowledge", response_class=HTMLResponse)
async def acknowledge(request: Request, context: ContextDep, mac: MacDep) -> HTMLResponse:
    await acknowledge_device(context.unit_of_work(), mac)
    return await _drawer(
        request, context, mac, {"devices-changed": None, "toast": "Marked as known"}
    )


@router.post("/devices/{mac}/forget", response_class=HTMLResponse)
async def forget(context: ContextDep, mac: MacDep) -> HTMLResponse:
    name = await forget_device(context.unit_of_work(), mac)
    triggers = {"devices-changed": None, "toast": f"Forgot {name}"}
    return HTMLResponse("", headers={"HX-Trigger": json.dumps(triggers)})


async def _drawer(
    request: Request, context: WebContext, mac: MacAddress, triggers: dict[str, str | None]
) -> HTMLResponse:
    now = context.clock.now()
    detail = await device_detail(context.unit_of_work(), mac, now, context.timezone)
    response = templates.TemplateResponse(
        request, "partials/drawer.html", {"drawer": drawer_view(detail, context.plugin_names, now)}
    )
    if triggers:
        response.headers["HX-Trigger"] = json.dumps(triggers)
    return response
