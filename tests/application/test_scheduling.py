import asyncio
import logging
from datetime import timedelta

import pytest

from network_monitor_tds.application.models import Backoff
from network_monitor_tds.application.scheduling import run_once, run_periodically, run_with_restarts
from tests.conftest import Stop

pytestmark = pytest.mark.anyio

LOGGER = logging.getLogger("tests.scheduling")
SECOND = timedelta(seconds=1)


class RecordingSleep:
    def __init__(self, limit: int) -> None:
        self.calls: list[float] = []
        self._limit = limit

    async def __call__(self, seconds: float) -> None:
        self.calls.append(seconds)
        if len(self.calls) >= self._limit:
            raise Stop


async def test_run_periodically_repeats_job_at_interval() -> None:
    runs: list[int] = []
    sleep = RecordingSleep(3)

    async def job() -> None:
        runs.append(1)

    with pytest.raises(Stop):
        await run_periodically(job, 30 * SECOND, SECOND, sleep, LOGGER)

    assert len(runs) == 3
    assert sleep.calls == [30.0, 30.0, 30.0]


async def test_run_once_logs_failures(caplog: pytest.LogCaptureFixture) -> None:
    async def job() -> None:
        raise RuntimeError

    await run_once(job, SECOND, LOGGER)

    assert "Failed" in caplog.text


async def test_run_once_times_out(caplog: pytest.LogCaptureFixture) -> None:
    async def job() -> None:
        await asyncio.sleep(10)

    await run_once(job, timedelta(milliseconds=10), LOGGER)

    assert "Timed out" in caplog.text


async def test_run_once_propagates_cancellation() -> None:
    async def job() -> None:
        raise asyncio.CancelledError

    with pytest.raises(asyncio.CancelledError):
        await run_once(job, SECOND, LOGGER)


async def test_run_with_restarts_backs_off_on_crashes_and_resets_after_clean_exit() -> None:
    outcomes = iter([RuntimeError, RuntimeError, RuntimeError, None, RuntimeError])
    sleep = RecordingSleep(5)

    async def job() -> None:
        outcome = next(outcomes)
        if outcome is not None:
            raise outcome

    with pytest.raises(Stop):
        await run_with_restarts(job, Backoff(SECOND, 3 * SECOND), sleep, LOGGER)

    assert sleep.calls == [1.0, 2.0, 3.0, 1.0, 1.0]
