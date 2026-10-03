from datetime import timedelta

from network_monitor_tds.application.models import PluginState, PluginStatus
from network_monitor_tds.domain.plugins.models import PluginId
from network_monitor_tds.plugins.host.status import StatusBoard
from tests.conftest import T0, FixedClock

DEMO = PluginId("demo")


def test_status_follows_reports() -> None:
    board = StatusBoard(FixedClock(T0 + timedelta(minutes=1)))
    reporter = board.reporter(DEMO)

    assert board.get(DEMO).state is PluginState.STOPPED
    reporter.running()
    assert board.get(DEMO) == PluginStatus(PluginState.RUNNING, None, None)
    reporter.failed("boom")
    assert board.get(DEMO) == PluginStatus(PluginState.FAILING, None, "boom")
    reporter.running()
    assert board.get(DEMO) == PluginStatus(PluginState.RUNNING, None, "boom")
    reporter.succeeded()
    assert board.get(DEMO) == PluginStatus(PluginState.RUNNING, T0 + timedelta(minutes=1), None)
    board.stopped(DEMO)
    assert board.get(DEMO).state is PluginState.STOPPED
