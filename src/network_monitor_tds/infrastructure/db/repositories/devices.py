from collections.abc import Sequence

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from network_monitor_tds.domain.devices.models import Device
from network_monitor_tds.domain.network.models import MacAddress
from network_monitor_tds.infrastructure.db.mappers import device_from_record, write_device
from network_monitor_tds.infrastructure.db.models import DeviceRecord


class SqlDeviceRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get(self, mac: MacAddress) -> Device | None:
        record = await self._session.get(DeviceRecord, mac)
        return None if record is None else device_from_record(record)

    async def list(self) -> Sequence[Device]:
        records = await self._session.scalars(select(DeviceRecord).order_by(DeviceRecord.mac))
        return [device_from_record(record) for record in records]

    async def save(self, device: Device) -> None:
        record = await self._session.get(DeviceRecord, device.mac) or DeviceRecord()
        self._session.add(write_device(record, device))
        await self._session.flush()

    async def delete(self, mac: MacAddress) -> None:
        await self._session.execute(delete(DeviceRecord).where(DeviceRecord.mac == mac))
