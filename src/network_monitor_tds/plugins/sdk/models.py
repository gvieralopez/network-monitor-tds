from dataclasses import dataclass
from datetime import timedelta
from enum import StrEnum

from pydantic import BaseModel, ConfigDict

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


class PluginSettings(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")


class ScheduledSettings(PluginSettings):
    interval: timedelta
    timeout: timedelta
