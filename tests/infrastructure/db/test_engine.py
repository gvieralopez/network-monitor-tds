from pathlib import Path

import pytest
from sqlalchemy import text

from network_monitor_tds.infrastructure.db.engine import sqlite_url
from tests.conftest import Database

pytestmark = pytest.mark.anyio


@pytest.mark.parametrize(
    ("pragma", "expected"),
    [("foreign_keys", 1), ("journal_mode", "wal"), ("synchronous", 1), ("busy_timeout", 5000)],
)
async def test_connections_apply_pragmas(
    empty_database: Database, pragma: str, expected: object
) -> None:
    async with empty_database.engine.connect() as connection:
        result = await connection.scalar(text(f"PRAGMA {pragma}"))

    assert result == expected


def test_sqlite_url() -> None:
    assert sqlite_url(Path("/data/nmtds.db")) == "sqlite+aiosqlite:////data/nmtds.db"
