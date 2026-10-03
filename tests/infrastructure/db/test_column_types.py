from datetime import UTC, datetime, timedelta, timezone
from ipaddress import IPv4Address

import pytest
from sqlalchemy.dialects import sqlite

from network_monitor_tds.domain.errors import NaiveDatetimeError
from network_monitor_tds.domain.network.models import MacAddress
from network_monitor_tds.infrastructure.db.column_types import (
    IPv4AddressType,
    MacAddressType,
    UTCDateTime,
)
from tests.conftest import NAIVE, T0

DIALECT = sqlite.dialect()
CET = timezone(timedelta(hours=2))


@pytest.mark.parametrize(
    ("value", "stored"),
    [
        (T0, datetime(2026, 10, 3, 12, 0)),
        (datetime(2026, 10, 3, 14, 0, tzinfo=CET), datetime(2026, 10, 3, 12, 0)),
        (None, None),
    ],
)
def test_utc_datetime_stores_naive_utc(value: datetime | None, stored: datetime | None) -> None:
    assert UTCDateTime().process_bind_param(value, DIALECT) == stored


def test_utc_datetime_rejects_naive_values() -> None:
    with pytest.raises(NaiveDatetimeError):
        UTCDateTime().process_bind_param(NAIVE, DIALECT)


@pytest.mark.parametrize(("stored", "value"), [(NAIVE, T0), (None, None)])
def test_utc_datetime_reads_as_utc(stored: datetime | None, value: datetime | None) -> None:
    result = UTCDateTime().process_result_value(stored, DIALECT)

    assert result == value
    assert result is None or result.tzinfo is UTC


@pytest.mark.parametrize(
    ("value", "stored"), [(MacAddress("24:0a:c4:9f:31:5e"), "24:0a:c4:9f:31:5e"), (None, None)]
)
def test_mac_address_round_trip(value: MacAddress | None, stored: str | None) -> None:
    column = MacAddressType()

    assert column.process_bind_param(value, DIALECT) == stored
    assert column.process_result_value(stored, DIALECT) == value


@pytest.mark.parametrize(
    ("value", "stored"), [(IPv4Address("192.168.1.10"), "192.168.1.10"), (None, None)]
)
def test_ipv4_address_round_trip(value: IPv4Address | None, stored: str | None) -> None:
    column = IPv4AddressType()

    assert column.process_bind_param(value, DIALECT) == stored
    assert column.process_result_value(stored, DIALECT) == value
