from collections.abc import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from network_monitor_tds.domain.plugins.models import PluginConfig, PluginId
from network_monitor_tds.infrastructure.db.mappers import (
    plugin_config_from_record,
    write_plugin_config,
)
from network_monitor_tds.infrastructure.db.models import PluginConfigRecord


class SqlPluginConfigRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get(self, plugin_id: PluginId) -> PluginConfig | None:
        record = await self._session.get(PluginConfigRecord, plugin_id)
        return None if record is None else plugin_config_from_record(record)

    async def list(self) -> Sequence[PluginConfig]:
        records = await self._session.scalars(
            select(PluginConfigRecord).order_by(PluginConfigRecord.plugin_id)
        )
        return [plugin_config_from_record(record) for record in records]

    async def save(self, config: PluginConfig) -> None:
        record = await self._session.get(PluginConfigRecord, config.plugin_id)
        self._session.add(write_plugin_config(record or PluginConfigRecord(), config))
        await self._session.flush()
