from dataclasses import dataclass
from datetime import timedelta

from network_monitor_tds.domain.devices.models import Category
from network_monitor_tds.domain.presence.errors import InvalidPolicyError


@dataclass(frozen=True, slots=True)
class PresencePolicy:
    sweep_interval: timedelta
    missed_sweeps: int
    mobile_missed_sweeps: int

    def __post_init__(self) -> None:
        if self.sweep_interval <= timedelta():
            raise InvalidPolicyError("sweep_interval must be positive")
        if min(self.missed_sweeps, self.mobile_missed_sweeps) < 1:
            raise InvalidPolicyError("missed sweep thresholds must be at least 1")

    def timeout_for(self, category: Category) -> timedelta:
        sweeps = self.mobile_missed_sweeps if category.is_mobile else self.missed_sweeps
        return self.sweep_interval * sweeps


DEFAULT_POLICY = PresencePolicy(
    sweep_interval=timedelta(minutes=5), missed_sweeps=2, mobile_missed_sweeps=3
)
