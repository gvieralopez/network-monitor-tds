import runpy

import pytest

from network_monitor_tds import __version__


def test_package_runs_as_module(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setattr("sys.argv", ["nmtds", "version"])

    with pytest.raises(SystemExit):
        runpy.run_module("network_monitor_tds", run_name="__main__")

    assert capsys.readouterr().out.strip() == __version__
