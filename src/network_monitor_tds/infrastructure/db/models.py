from datetime import datetime
from ipaddress import IPv4Address
from typing import Any, ClassVar

from sqlalchemy import JSON, ForeignKey, Index, MetaData, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from network_monitor_tds.domain.network.models import MacAddress
from network_monitor_tds.infrastructure.db.column_types import (
    IPv4AddressType,
    MacAddressType,
    UTCDateTime,
)

NAMING_CONVENTION = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}

DEVICE_FK = "devices.mac"


class Base(DeclarativeBase):
    metadata = MetaData(naming_convention=NAMING_CONVENTION)
    type_annotation_map: ClassVar[dict[Any, Any]] = {
        datetime: UTCDateTime,
        MacAddress: MacAddressType,
        IPv4Address: IPv4AddressType,
    }


class DeviceRecord(Base):
    __tablename__ = "devices"

    mac: Mapped[MacAddress] = mapped_column(primary_key=True)
    ip: Mapped[IPv4Address | None]
    first_seen: Mapped[datetime]
    last_seen: Mapped[datetime] = mapped_column(index=True)
    acknowledged: Mapped[bool]
    label_name: Mapped[str | None] = mapped_column(String(100))
    label_category: Mapped[str | None] = mapped_column(String(20))
    label_icon: Mapped[str | None] = mapped_column(String(40))


class FactRecord(Base):
    __tablename__ = "facts"

    mac: Mapped[MacAddress] = mapped_column(
        ForeignKey(DEVICE_FK, ondelete="CASCADE"), primary_key=True
    )
    name: Mapped[str] = mapped_column(String(64), primary_key=True)
    value: Mapped[str] = mapped_column(Text)
    source: Mapped[str] = mapped_column(String(64))
    observed_at: Mapped[datetime]


class DetectionRecord(Base):
    __tablename__ = "detections"

    mac: Mapped[MacAddress] = mapped_column(
        ForeignKey(DEVICE_FK, ondelete="CASCADE"), primary_key=True
    )
    source: Mapped[str] = mapped_column(String(64), primary_key=True)
    first_seen: Mapped[datetime]
    last_seen: Mapped[datetime]


class PresenceRecord(Base):
    __tablename__ = "presence"

    mac: Mapped[MacAddress] = mapped_column(
        ForeignKey(DEVICE_FK, ondelete="CASCADE"), primary_key=True
    )
    state: Mapped[str] = mapped_column(String(16))
    changed_at: Mapped[datetime]
    last_seen: Mapped[datetime]


class PresenceIntervalRecord(Base):
    __tablename__ = "presence_intervals"
    __table_args__ = (Index("ix_presence_intervals_mac_started_at", "mac", "started_at"),)

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    mac: Mapped[MacAddress] = mapped_column(ForeignKey(DEVICE_FK, ondelete="CASCADE"))
    started_at: Mapped[datetime]
    ended_at: Mapped[datetime | None]


class EventRecord(Base):
    __tablename__ = "events"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    kind: Mapped[str] = mapped_column(String(32))
    mac: Mapped[MacAddress] = mapped_column(ForeignKey(DEVICE_FK, ondelete="CASCADE"))
    occurred_at: Mapped[datetime] = mapped_column(index=True)


class PluginConfigRecord(Base):
    __tablename__ = "plugin_configs"

    plugin_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    enabled: Mapped[bool]
    settings: Mapped[dict[str, Any]] = mapped_column(JSON)
    updated_at: Mapped[datetime]
