from pydantic import BaseModel, ConfigDict, field_validator

from network_monitor_tds.domain.devices.models import Category, DeviceLabels
from network_monitor_tds.web.drawings import DRAWING_NAMES


class LabelsForm(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    name: str = ""
    category: Category | None = None
    icon: str | None = None

    @field_validator("category", "icon", mode="before")
    @classmethod
    def blank_means_automatic(cls, value: object) -> object:
        return None if value == "" else value

    @field_validator("icon")
    @classmethod
    def known_icon(cls, value: str | None) -> str | None:
        if value is not None and value not in DRAWING_NAMES:
            message = f"Unknown icon {value!r}"
            raise ValueError(message)
        return value

    def to_labels(self) -> DeviceLabels:
        return DeviceLabels(name=self.name.strip() or None, category=self.category, icon=self.icon)
