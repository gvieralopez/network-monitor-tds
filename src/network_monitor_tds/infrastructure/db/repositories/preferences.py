from collections.abc import Mapping
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession

from network_monitor_tds.domain.plugins.models import JsonValue
from network_monitor_tds.infrastructure.db.models import PreferenceRecord


class SqlPreferenceRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get(self, key: str) -> Mapping[str, JsonValue] | None:
        record = await self._session.get(PreferenceRecord, key)
        return None if record is None else record.value

    async def save(self, key: str, value: Mapping[str, JsonValue], updated_at: datetime) -> None:
        record = await self._session.get(PreferenceRecord, key) or PreferenceRecord(key=key)
        record.value = dict(value)
        record.updated_at = updated_at
        self._session.add(record)
        await self._session.flush()
