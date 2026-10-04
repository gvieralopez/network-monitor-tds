import subprocess
import sys

import pytest

from network_monitor_tds import server
from network_monitor_tds.settings import AppSettings

LOADED_HEAVY_MODULES = """
import sys
import network_monitor_tds.server
print(sorted({name.split(".")[0] for name in sys.modules} & {"alembic", "typer"}))
"""


def test_main_serves_with_settings_from_the_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    served: list[AppSettings] = []

    async def fake_serve(settings: AppSettings) -> None:
        served.append(settings)

    monkeypatch.setattr(server, "serve", fake_serve)

    server.main()

    assert served == [AppSettings()]


def test_server_never_loads_the_cli_or_migrations() -> None:
    """The long-running process stays lean: alembic and typer cost about 19 MiB together."""
    result = subprocess.run(
        [sys.executable, "-c", LOADED_HEAVY_MODULES], capture_output=True, text=True, check=True
    )
    assert result.stdout.strip() == "[]"
