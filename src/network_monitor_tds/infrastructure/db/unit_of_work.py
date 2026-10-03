from collections.abc import Callable
from types import TracebackType
from typing import Self

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from network_monitor_tds.infrastructure.db.repositories.detections import SqlDetectionRepository
from network_monitor_tds.infrastructure.db.repositories.devices import SqlDeviceRepository
from network_monitor_tds.infrastructure.db.repositories.events import SqlEventRepository
from network_monitor_tds.infrastructure.db.repositories.facts import SqlFactRepository
from network_monitor_tds.infrastructure.db.repositories.plugin_configs import (
    SqlPluginConfigRepository,
)
from network_monitor_tds.infrastructure.db.repositories.presence import SqlPresenceRepository


def unit_of_work_factory(
    session_factory: async_sessionmaker[AsyncSession],
) -> Callable[[], SqlUnitOfWork]:
    return lambda: SqlUnitOfWork(session_factory())


class SqlUnitOfWork:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self.devices = SqlDeviceRepository(session)
        self.facts = SqlFactRepository(session)
        self.detections = SqlDetectionRepository(session)
        self.presence = SqlPresenceRepository(session)
        self.events = SqlEventRepository(session)
        self.plugin_configs = SqlPluginConfigRepository(session)

    async def __aenter__(self) -> Self:
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        await self._session.rollback()
        await self._session.close()

    async def commit(self) -> None:
        await self._session.commit()
