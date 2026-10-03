import asyncio
import logging
import sqlite3
from contextlib import closing
from pathlib import Path

from alembic import command
from alembic.config import Config
from alembic.runtime.migration import MigrationContext
from alembic.script import ScriptDirectory
from sqlalchemy import Connection
from sqlalchemy.ext.asyncio import AsyncEngine

from network_monitor_tds.infrastructure.db.errors import UnknownSchemaRevisionError

logger = logging.getLogger(__name__)

MIGRATIONS_DIR = Path(__file__).parent / "migrations"


async def upgrade_to_head(engine: AsyncEngine, database_path: Path) -> None:
    config = alembic_config()
    script = ScriptDirectory.from_config(config)
    current = await current_revision(engine)
    if current == script.get_current_head():
        return
    if current is not None:
        _ensure_known(script, current)
        backup = backup_path(database_path, current)
        logger.info("Backing up the database to %s before migrating", backup)
        await asyncio.to_thread(backup_database, database_path, backup)
    logger.info("Migrating the database from %s to %s", current, script.get_current_head())
    async with engine.begin() as connection:
        await connection.run_sync(_upgrade, config)


def alembic_config() -> Config:
    config = Config()
    config.set_main_option("script_location", str(MIGRATIONS_DIR))
    return config


async def current_revision(engine: AsyncEngine) -> str | None:
    async with engine.connect() as connection:
        return await connection.run_sync(_read_revision)


def backup_path(database_path: Path, revision: str) -> Path:
    return database_path.with_name(f"{database_path.name}.bak-{revision}")


def backup_database(source: Path, target: Path) -> None:
    with closing(sqlite3.connect(source)) as origin, closing(sqlite3.connect(target)) as copy:
        origin.backup(copy)


def _read_revision(connection: Connection) -> str | None:
    return MigrationContext.configure(connection).get_current_revision()


def _ensure_known(script: ScriptDirectory, revision: str) -> None:
    if revision not in {known.revision for known in script.walk_revisions()}:
        raise UnknownSchemaRevisionError(revision)


def _upgrade(connection: Connection, config: Config) -> None:
    config.attributes["connection"] = connection
    command.upgrade(config, "head")
