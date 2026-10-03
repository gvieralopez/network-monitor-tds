from datetime import datetime, timedelta

from network_monitor_tds.application.ports import UnitOfWork
from network_monitor_tds.domain.presence.policy import DEFAULT_POLICY, PresencePolicy

PRESENCE_KEY = "presence"


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
