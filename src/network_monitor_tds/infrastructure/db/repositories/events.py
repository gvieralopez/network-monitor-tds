from collections.abc import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from network_monitor_tds.domain.events.models import DeviceEvent
from network_monitor_tds.infrastructure.db.mappers import event_from_record, event_record
from network_monitor_tds.infrastructure.db.models import EventRecord


class SqlEventRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add(self, event: DeviceEvent) -> None:
        self._session.add(event_record(event))
        await self._session.flush()

    async def recent(self, limit: int) -> Sequence[DeviceEvent]:
        records = await self._session.scalars(
            select(EventRecord)
            .order_by(EventRecord.occurred_at.desc(), EventRecord.id.desc())
            .limit(limit)
        )
        return [event_from_record(record) for record in records]
