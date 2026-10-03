from dataclasses import dataclass
from datetime import timedelta

from network_monitor_tds.domain.devices.models import Category
from network_monitor_tds.domain.presence.errors import InvalidPolicyError


@dataclass(frozen=True, slots=True)
class PresencePolicy:
    offline_after: timedelta
    mobile_offline_after: timedelta

    def __post_init__(self) -> None:
        if min(self.offline_after, self.mobile_offline_after) <= timedelta():
            raise InvalidPolicyError("offline thresholds must be positive")

    def timeout_for(self, category: Category) -> timedelta:
        return self.mobile_offline_after if category.is_mobile else self.offline_after


DEFAULT_POLICY = PresencePolicy(
    offline_after=timedelta(minutes=10), mobile_offline_after=timedelta(minutes=15)
)
