from collections.abc import Mapping
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


class PluginPurpose(StrEnum):
    PASSIVE_DISCOVERY = "passive_discovery"
    ACTIVE_DISCOVERY = "active_discovery"
    INTEGRATION = "integration"
    METADATA = "metadata"
    DEVELOPMENT = "development"


@dataclass(frozen=True, slots=True)
class PluginInfo:
    plugin_id: PluginId
    name: str
    description: str
    enabled_by_default: bool
    purpose: PluginPurpose


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

    @classmethod
    def setup_fields(cls) -> frozenset[str]:
        return frozenset()

    @classmethod
    def placeholders(cls) -> Mapping[str, str]:
        return {}


class ScheduledSettings(PluginSettings):
    interval: timedelta
    timeout: timedelta
