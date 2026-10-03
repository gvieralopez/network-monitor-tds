from typing import Annotated, cast

from fastapi import Depends, HTTPException, Request, status

from network_monitor_tds.domain.network.errors import InvalidMacAddressError
from network_monitor_tds.domain.network.models import MacAddress
from network_monitor_tds.web.models import WebContext


def get_context(request: Request) -> WebContext:
    return cast(WebContext, request.app.state.context)


def parse_mac(mac: str) -> MacAddress:
    try:
        return MacAddress.parse(mac)
    except InvalidMacAddressError as error:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(error)) from error


ContextDep = Annotated[WebContext, Depends(get_context)]
MacDep = Annotated[MacAddress, Depends(parse_mac)]
