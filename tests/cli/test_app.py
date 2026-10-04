from pathlib import Path

import pytest
from alembic.script import ScriptDirectory
from typer.testing import CliRunner

from network_monitor_tds import __version__
from network_monitor_tds.cli.app import app
from network_monitor_tds.infrastructure.db.migrator import alembic_config

runner = CliRunner()


def test_version() -> None:
    result = runner.invoke(app, ["version"])

    assert result.exit_code == 0
    assert result.output.strip() == __version__


def test_db_current_without_database(data_dir: Path) -> None:
    result = runner.invoke(app, ["db", "current"])

    assert result.exit_code == 0
    assert "No database" in result.output
    assert not data_dir.exists()


def test_db_upgrade_then_current(data_dir: Path) -> None:
    upgrade = runner.invoke(app, ["db", "upgrade"])
    current = runner.invoke(app, ["db", "current"])

    head = ScriptDirectory.from_config(alembic_config()).get_current_head()
    assert upgrade.output.strip() == f"Database is at revision {head}"
    assert current.output.strip() == head
    assert (data_dir / "nmtds.db").exists()


@pytest.mark.usefixtures("data_dir")
def test_plugins_list_enable_and_disable() -> None:
    listed = runner.invoke(app, ["plugins", "list"]).output.splitlines()
    assert [line.split()[:2] for line in listed] == [
        ["on", "arp-listen"],
        ["on", "arp-sweep"],
        ["off", "demo"],
        ["on", "dhcp-sniff"],
        ["on", "oui"],
        ["off", "technitium"],
    ]

    enabled = runner.invoke(app, ["plugins", "enable", "demo"])
    relisted = runner.invoke(app, ["plugins", "list"])
    disabled = runner.invoke(app, ["plugins", "disable", "demo"])

    assert enabled.output.strip() == "demo is on"
    assert "on  demo" in relisted.output
    assert disabled.output.strip() == "demo is off"


@pytest.mark.usefixtures("data_dir")
def test_plugins_set_and_show_settings() -> None:
    result = runner.invoke(
        app, ["plugins", "set", "technitium", "url=http://dns:5380/", "token=s3cret"]
    )
    shown = runner.invoke(app, ["plugins", "show", "technitium"])

    assert result.exit_code == 0
    assert "url = http://dns:5380" in result.output
    assert "token = ********" in shown.output
    assert "s3cret" not in result.output + shown.output
    assert "Restart nmtds serve" in result.output


@pytest.mark.usefixtures("data_dir")
@pytest.mark.parametrize(
    ("arguments", "exit_code", "message"),
    [
        (["plugins", "set", "technitium", "colour=blue"], 1, "Extra inputs are not permitted"),
        (["plugins", "set", "technitium", "url=ftp://dns"], 1, "must start with http"),
        (["plugins", "set", "technitium", "oops"], 2, "Expected key=value, got: oops"),
        (["plugins", "show", "nope"], 1, "No plugin is installed with id 'nope'"),
    ],
)
def test_plugins_set_rejects_bad_input(arguments: list[str], exit_code: int, message: str) -> None:
    result = runner.invoke(app, arguments)

    assert result.exit_code == exit_code
    assert message in result.output


@pytest.mark.usefixtures("data_dir")
def test_enabling_unknown_plugin_fails() -> None:
    result = runner.invoke(app, ["plugins", "enable", "nope"])

    assert result.exit_code == 1
    assert "No plugin is installed with id 'nope'" in result.output


def test_no_arguments_shows_help() -> None:
    result = runner.invoke(app, [])

    assert "serve" in result.output
