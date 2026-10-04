from datetime import datetime

from network_monitor_tds.application.models import PruneResult
from network_monitor_tds.application.ports import UnitOfWork
from network_monitor_tds.domain.retention.models import RetentionPolicy


async def prune_history(uow: UnitOfWork, policy: RetentionPolicy, now: datetime) -> PruneResult:
    cutoff = policy.cutoff(now)
    async with uow:
        intervals = await uow.presence.delete_intervals_ended_before(cutoff)
        events = await uow.events.delete_before(cutoff)
        await uow.commit()
    return PruneResult(intervals=intervals, events=events)
