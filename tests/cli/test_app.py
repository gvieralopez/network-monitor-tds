from pathlib import Path

import pytest
from typer.testing import CliRunner

from network_monitor_tds import __version__
from network_monitor_tds.cli.app import app

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

    assert upgrade.output.strip() == "Database is at revision 0001"
    assert current.output.strip() == "0001"
    assert (data_dir / "nmtds.db").exists()


@pytest.mark.usefixtures("data_dir")
def test_plugins_list_enable_and_disable() -> None:
    assert runner.invoke(app, ["plugins", "list"]).output.split() == [
        "off",
        "demo",
        "Demo",
        "network",
    ]

    enabled = runner.invoke(app, ["plugins", "enable", "demo"])
    listed = runner.invoke(app, ["plugins", "list"])
    disabled = runner.invoke(app, ["plugins", "disable", "demo"])

    assert enabled.output.strip() == "demo is on"
    assert listed.output.split()[0] == "on"
    assert disabled.output.strip() == "demo is off"


@pytest.mark.usefixtures("data_dir")
def test_enabling_unknown_plugin_fails() -> None:
    result = runner.invoke(app, ["plugins", "enable", "nope"])

    assert result.exit_code == 1
    assert "No plugin is installed with id 'nope'" in result.output


def test_no_arguments_shows_help() -> None:
    result = runner.invoke(app, [])

    assert "serve" in result.output
