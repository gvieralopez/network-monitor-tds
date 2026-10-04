import asyncio
import logging
from collections.abc import Awaitable, Callable
from datetime import timedelta
from typing import Protocol, override

from network_monitor_tds.application.models import Backoff
from network_monitor_tds.errors import NetworkMonitorError

type Job = Callable[[], Awaitable[None]]
type Sleep = Callable[[float], Awaitable[None]]


class Reporter(Protocol):
    def running(self) -> None: ...
    def succeeded(self) -> None: ...
    def failed(self, reason: str) -> None: ...


class SilentReporter(Reporter):
    @override
    def running(self) -> None:
        return None

    @override
    def succeeded(self) -> None:
        return None

    @override
    def failed(self, reason: str) -> None:
        return None


SILENT = SilentReporter()


async def run_periodically(
    job: Job,
    interval: timedelta,
    timeout: timedelta,
    sleep: Sleep,
    logger: logging.Logger,
    reporter: Reporter,
) -> None:
    while True:
        await run_once(job, timeout, logger, reporter)
        await sleep(interval.total_seconds())


async def run_once(
    job: Job, timeout: timedelta, logger: logging.Logger, reporter: Reporter
) -> None:
    reporter.running()
    try:
        async with asyncio.timeout(timeout.total_seconds()):
            await job()
    except TimeoutError:
        logger.warning("Timed out after %s", timeout)
        reporter.failed(f"Timed out after {timeout}")
    except NetworkMonitorError as error:
        logger.error("Failed: %s", error)
        reporter.failed(str(error))
    except Exception as error:
        logger.exception("Failed")
        reporter.failed(_describe(error))
    else:
        reporter.succeeded()


async def run_with_restarts(
    job: Job, backoff: Backoff, sleep: Sleep, logger: logging.Logger, reporter: Reporter
) -> None:
    delay = backoff.initial
    while True:
        reporter.running()
        try:
            await job()
        except Exception as error:
            _log_crash(logger, error, delay)
            reporter.failed(_describe(error))
            await sleep(delay.total_seconds())
            delay = min(delay * 2, backoff.maximum)
        else:
            logger.warning("Stopped unexpectedly; restarting in %s", backoff.initial)
            reporter.failed("Stopped unexpectedly")
            await sleep(backoff.initial.total_seconds())
            delay = backoff.initial


def _describe(error: Exception) -> str:
    return str(error) or type(error).__name__


def _log_crash(logger: logging.Logger, error: Exception, delay: timedelta) -> None:
    if isinstance(error, NetworkMonitorError):
        logger.error("Crashed: %s; restarting in %s", error, delay)
    else:
        logger.error("Crashed; restarting in %s", delay, exc_info=error)
