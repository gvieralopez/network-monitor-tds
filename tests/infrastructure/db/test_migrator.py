import sqlite3
from contextlib import closing
from pathlib import Path
from tempfile import TemporaryDirectory

import pytest
from alembic import command
from alembic.autogenerate import compare_metadata
from alembic.runtime.migration import MigrationContext
from alembic.script import ScriptDirectory
from sqlalchemy import Connection, inspect, text

from network_monitor_tds.infrastructure.db.errors import UnknownSchemaRevisionError
from network_monitor_tds.infrastructure.db.migrator import (
    alembic_config,
    backup_database,
    backup_path,
    current_revision,
    upgrade_to_head,
)
from network_monitor_tds.infrastructure.db.models import Base
from tests.conftest import Database

pytestmark = pytest.mark.anyio

HEAD = ScriptDirectory.from_config(alembic_config()).get_current_head()
TABLES = {
    "alembic_version",
    "devices",
    "facts",
    "detections",
    "presence",
    "presence_intervals",
    "events",
    "plugin_configs",
    "preferences",
}


async def test_upgrade_creates_schema_at_head(empty_database: Database) -> None:
    await upgrade_to_head(empty_database.engine, empty_database.path)

    async with empty_database.engine.connect() as connection:
        tables = await connection.run_sync(lambda sync: set(inspect(sync).get_table_names()))
    assert tables == TABLES
    assert await current_revision(empty_database.engine) == HEAD


async def test_migrated_schema_matches_models(database: Database) -> None:
    async with database.engine.connect() as connection:
        differences = await connection.run_sync(_schema_differences)

    assert differences == []


async def test_upgrade_at_head_is_a_no_op(database: Database) -> None:
    await upgrade_to_head(database.engine, database.path)

    assert list(database.path.parent.glob("*.bak-*")) == []


async def test_upgrade_backs_up_before_migrating(
    database: Database, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(ScriptDirectory, "get_current_head", lambda _: "9999")

    await upgrade_to_head(database.engine, database.path)

    assert backup_path(database.path, str(HEAD)).exists()


async def test_upgrade_refuses_unknown_revision(database: Database) -> None:
    async with database.engine.begin() as connection:
        await connection.execute(text("UPDATE alembic_version SET version_num = 'from-the-future'"))

    with pytest.raises(UnknownSchemaRevisionError, match="from-the-future"):
        await upgrade_to_head(database.engine, database.path)


async def test_downgrade_to_base_and_back(database: Database) -> None:
    async with database.engine.begin() as connection:
        await connection.run_sync(_downgrade, "base")
    assert await current_revision(database.engine) is None

    await upgrade_to_head(database.engine, database.path)

    assert await current_revision(database.engine) == HEAD


def test_backup_path() -> None:
    assert backup_path(Path("/data/nmtds.db"), "0001") == Path("/data/nmtds.db.bak-0001")


def test_backup_database_copies_content() -> None:
    with TemporaryDirectory() as directory:
        source, target = Path(directory) / "source.db", Path(directory) / "target.db"
        with closing(sqlite3.connect(source)) as connection:
            connection.execute("CREATE TABLE things (name TEXT)")
            connection.execute("INSERT INTO things VALUES ('lamp')")
            connection.commit()

        backup_database(source, target)

        with closing(sqlite3.connect(target)) as connection:
            assert connection.execute("SELECT name FROM things").fetchall() == [("lamp",)]


def _schema_differences(connection: Connection) -> list[object]:
    context = MigrationContext.configure(connection)
    return list(compare_metadata(context, Base.metadata))


def _downgrade(connection: Connection, revision: str) -> None:
    config = alembic_config()
    config.attributes["connection"] = connection
    command.downgrade(config, revision)
