from datetime import datetime, timedelta

from network_monitor_tds.application.ports import UnitOfWork
from network_monitor_tds.domain.presence.policy import DEFAULT_POLICY, PresencePolicy
from network_monitor_tds.domain.retention.models import DEFAULT_RETENTION, RetentionPolicy

PRESENCE_KEY = "presence"
RETENTION_KEY = "retention"


async def load_presence_policy(uow: UnitOfWork) -> PresencePolicy:
    async with uow:
        stored = await uow.preferences.get(PRESENCE_KEY)
    if stored is None:
        return DEFAULT_POLICY
    return PresencePolicy(
        offline_after=timedelta(seconds=float(str(stored["offline_after_seconds"]))),
        mobile_offline_after=timedelta(seconds=float(str(stored["mobile_offline_after_seconds"]))),
    )


async def save_presence_policy(uow: UnitOfWork, policy: PresencePolicy, now: datetime) -> None:
    value = {
        "offline_after_seconds": policy.offline_after.total_seconds(),
        "mobile_offline_after_seconds": policy.mobile_offline_after.total_seconds(),
    }
    async with uow:
        await uow.preferences.save(PRESENCE_KEY, value, now)
        await uow.commit()


async def load_retention_policy(uow: UnitOfWork) -> RetentionPolicy:
    async with uow:
        stored = await uow.preferences.get(RETENTION_KEY)
    if stored is None:
        return DEFAULT_RETENTION
    return RetentionPolicy(keep_days=int(str(stored["keep_days"])))


async def save_retention_policy(uow: UnitOfWork, policy: RetentionPolicy, now: datetime) -> None:
    async with uow:
        await uow.preferences.save(RETENTION_KEY, {"keep_days": policy.keep_days}, now)
        await uow.commit()
