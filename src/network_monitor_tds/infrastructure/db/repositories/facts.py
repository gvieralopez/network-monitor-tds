from collections import defaultdict
from collections.abc import Mapping

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from network_monitor_tds.domain.network.models import MacAddress
from network_monitor_tds.domain.observations.models import Fact
from network_monitor_tds.infrastructure.db.mappers import fact_from_record, write_fact
from network_monitor_tds.infrastructure.db.models import FactRecord


class SqlFactRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def for_device(self, mac: MacAddress) -> dict[str, Fact]:
        records = await self._session.scalars(select(FactRecord).where(FactRecord.mac == mac))
        return {record.name: fact_from_record(record) for record in records}

    async def all(self) -> dict[MacAddress, dict[str, Fact]]:
        facts: defaultdict[MacAddress, dict[str, Fact]] = defaultdict(dict)
        for record in await self._session.scalars(select(FactRecord)):
            facts[record.mac][record.name] = fact_from_record(record)
        return dict(facts)

    async def save(self, mac: MacAddress, facts: Mapping[str, Fact]) -> None:
        for fact in facts.values():
            record = await self._session.get(FactRecord, (mac, fact.name)) or FactRecord()
            self._session.add(write_fact(record, mac, fact))
        await self._session.flush()
