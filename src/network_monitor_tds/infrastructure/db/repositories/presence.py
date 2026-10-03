from collections import defaultdict
from datetime import datetime

from sqlalchemy import or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from network_monitor_tds.domain.network.models import MacAddress
from network_monitor_tds.domain.presence.models import Presence, PresenceInterval
from network_monitor_tds.infrastructure.db.mappers import (
    interval_from_record,
    interval_record,
    presence_from_record,
    write_presence,
)
from network_monitor_tds.infrastructure.db.models import PresenceIntervalRecord, PresenceRecord


class SqlPresenceRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get(self, mac: MacAddress) -> Presence | None:
        record = await self._session.get(PresenceRecord, mac)
        return None if record is None else presence_from_record(record)

    async def all(self) -> dict[MacAddress, Presence]:
        records = await self._session.scalars(select(PresenceRecord))
        return {record.mac: presence_from_record(record) for record in records}

    async def save(self, mac: MacAddress, presence: Presence) -> None:
        record = await self._session.get(PresenceRecord, mac) or PresenceRecord()
        self._session.add(write_presence(record, mac, presence))
        await self._session.flush()

    async def open_interval(self, mac: MacAddress, start: datetime) -> None:
        self._session.add(interval_record(mac, start))
        await self._session.flush()

    async def close_interval(self, mac: MacAddress, end: datetime) -> None:
        await self._session.execute(
            update(PresenceIntervalRecord)
            .where(PresenceIntervalRecord.mac == mac, PresenceIntervalRecord.ended_at.is_(None))
            .values(ended_at=end)
        )

    async def intervals_since(self, since: datetime) -> dict[MacAddress, list[PresenceInterval]]:
        records = await self._session.scalars(
            select(PresenceIntervalRecord)
            .where(
                or_(
                    PresenceIntervalRecord.ended_at.is_(None),
                    PresenceIntervalRecord.ended_at >= since,
                )
            )
            .order_by(PresenceIntervalRecord.mac, PresenceIntervalRecord.started_at)
        )
        intervals: defaultdict[MacAddress, list[PresenceInterval]] = defaultdict(list)
        for record in records:
            intervals[record.mac].append(interval_from_record(record))
        return dict(intervals)
