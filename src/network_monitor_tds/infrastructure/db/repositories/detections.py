from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from network_monitor_tds.domain.network.models import MacAddress
from network_monitor_tds.domain.observations.models import Detection
from network_monitor_tds.domain.plugins.models import PluginId
from network_monitor_tds.infrastructure.db.mappers import detection_from_record, write_detection
from network_monitor_tds.infrastructure.db.models import DetectionRecord


class SqlDetectionRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def for_device(self, mac: MacAddress) -> dict[PluginId, Detection]:
        records = await self._session.scalars(
            select(DetectionRecord)
            .where(DetectionRecord.mac == mac)
            .order_by(DetectionRecord.first_seen)
        )
        detections = (detection_from_record(record) for record in records)
        return {detection.source: detection for detection in detections}

    async def save(self, mac: MacAddress, detection: Detection) -> None:
        key = (mac, detection.source)
        record = await self._session.get(DetectionRecord, key) or DetectionRecord()
        self._session.add(write_detection(record, mac, detection))
        await self._session.flush()
