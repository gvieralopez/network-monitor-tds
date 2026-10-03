from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime
from typing import NewType

from network_monitor_tds.domain.time import ensure_aware

PluginId = NewType("PluginId", str)

type JsonValue = str | int | float | bool | list[JsonValue] | dict[str, JsonValue] | None


@dataclass(frozen=True, slots=True)
class PluginConfig:
    plugin_id: PluginId
    enabled: bool
    settings: Mapping[str, JsonValue]
    updated_at: datetime

    def __post_init__(self) -> None:
        ensure_aware(self.updated_at)


@dataclass(frozen=True, slots=True)
class PluginDefaults:
    enabled: bool
    settings: Mapping[str, JsonValue]
