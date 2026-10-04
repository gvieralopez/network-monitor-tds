from pathlib import Path

from sqlalchemy import event
from sqlalchemy.engine.interfaces import DBAPIConnection
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import ConnectionPoolEntry

PRAGMAS = (
    "PRAGMA foreign_keys = ON",
    "PRAGMA journal_mode = WAL",
    "PRAGMA synchronous = NORMAL",
    "PRAGMA busy_timeout = 5000",
)


def create_engine(database_path: Path) -> AsyncEngine:
    engine = create_async_engine(sqlite_url(database_path))
    event.listen(engine.sync_engine, "connect", _apply_pragmas)
    return engine


def sqlite_url(database_path: Path) -> str:
    return f"sqlite+aiosqlite:///{database_path}"


def create_session_factory(engine: AsyncEngine) -> async_sessionmaker[AsyncSession]:
    return async_sessionmaker(engine, expire_on_commit=False)


def _apply_pragmas(connection: DBAPIConnection, _record: ConnectionPoolEntry) -> None:
    cursor = connection.cursor()
    for pragma in PRAGMAS:
        cursor.execute(pragma)
    cursor.close()
