from pathlib import Path

import pytest

from network_monitor_tds.settings import AppSettings


def test_defaults() -> None:
    settings = AppSettings()

    assert settings.database_path == Path("data") / "nmtds.db"


def test_reads_prefixed_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("NMTDS_DATA_DIR", "/var/lib/nmtds")
    monkeypatch.setenv("NMTDS_OBSERVATION_QUEUE_SIZE", "50")

    settings = AppSettings()

    assert settings.database_path == Path("/var/lib/nmtds/nmtds.db")
    assert settings.observation_queue_size == 50
