import asyncio
import logging
from collections.abc import Awaitable, Callable
from datetime import timedelta

from network_monitor_tds.application.models import Backoff

type Job = Callable[[], Awaitable[None]]
type Sleep = Callable[[float], Awaitable[None]]


async def run_periodically(
    job: Job, interval: timedelta, timeout: timedelta, sleep: Sleep, logger: logging.Logger
) -> None:
    while True:
        await run_once(job, timeout, logger)
        await sleep(interval.total_seconds())


async def run_once(job: Job, timeout: timedelta, logger: logging.Logger) -> None:
    try:
        async with asyncio.timeout(timeout.total_seconds()):
            await job()
    except TimeoutError:
        logger.warning("Timed out after %s", timeout)
    except Exception:
        logger.exception("Failed")


async def run_with_restarts(
    job: Job, backoff: Backoff, sleep: Sleep, logger: logging.Logger
) -> None:
    delay = backoff.initial
    while True:
        try:
            await job()
        except Exception:
            logger.exception("Crashed; restarting in %s", delay)
            await sleep(delay.total_seconds())
            delay = min(delay * 2, backoff.maximum)
        else:
            logger.warning("Stopped unexpectedly; restarting in %s", backoff.initial)
            await sleep(backoff.initial.total_seconds())
            delay = backoff.initial
