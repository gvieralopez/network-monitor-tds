from datetime import UTC, datetime
from ipaddress import IPv4Address
from typing import override

from sqlalchemy import DateTime, Dialect, String
from sqlalchemy.types import TypeDecorator

from network_monitor_tds.domain.network.models import MacAddress
from network_monitor_tds.domain.time import ensure_aware


class UTCDateTime(TypeDecorator[datetime]):
    impl = DateTime
    cache_ok = True

    @override
    def process_bind_param(self, value: datetime | None, dialect: Dialect) -> datetime | None:
        if value is None:
            return None
        return ensure_aware(value).astimezone(UTC).replace(tzinfo=None)

    @override
    def process_result_value(self, value: datetime | None, dialect: Dialect) -> datetime | None:
        return None if value is None else value.replace(tzinfo=UTC)


class MacAddressType(TypeDecorator[MacAddress]):
    impl = String(17)
    cache_ok = True

    @override
    def process_bind_param(self, value: MacAddress | None, dialect: Dialect) -> str | None:
        return None if value is None else value.value

    @override
    def process_result_value(self, value: str | None, dialect: Dialect) -> MacAddress | None:
        return None if value is None else MacAddress(value)


class IPv4AddressType(TypeDecorator[IPv4Address]):
    impl = String(15)
    cache_ok = True

    @override
    def process_bind_param(self, value: IPv4Address | None, dialect: Dialect) -> str | None:
        return None if value is None else str(value)

    @override
    def process_result_value(self, value: str | None, dialect: Dialect) -> IPv4Address | None:
        return None if value is None else IPv4Address(value)
