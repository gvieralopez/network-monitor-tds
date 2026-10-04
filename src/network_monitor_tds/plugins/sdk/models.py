from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import StrEnum
from ipaddress import IPv4Address

from pydantic import BaseModel, ConfigDict

from network_monitor_tds.domain.network.models import MacAddress
from network_monitor_tds.domain.plugins.models import PluginId


class PluginKind(StrEnum):
    LISTENER = "listener"
    SCHEDULED = "scheduled"
    ENRICHMENT = "enrichment"


@dataclass(frozen=True, slots=True)
class PluginInfo:
    plugin_id: PluginId
    name: str
    description: str
    enabled_by_default: bool


@dataclass(frozen=True, slots=True)
class KnownDevice:
    mac: MacAddress
    ip: IPv4Address | None
    last_seen: datetime


class PluginSettings(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    @classmethod
    def secret_fields(cls) -> frozenset[str]:
        return frozenset(name for name, field in cls.model_fields.items() if not field.repr)


class ScheduledSettings(PluginSettings):
    interval: timedelta
    timeout: timedelta
