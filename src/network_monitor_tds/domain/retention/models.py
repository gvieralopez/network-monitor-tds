from dataclasses import dataclass
from datetime import datetime, timedelta

from network_monitor_tds.domain.retention.errors import InvalidRetentionError

MIN_KEEP_DAYS = 14
MAX_KEEP_DAYS = 3650


@dataclass(frozen=True, slots=True)
class RetentionPolicy:
    keep_days: int

    def __post_init__(self) -> None:
        if not MIN_KEEP_DAYS <= self.keep_days <= MAX_KEEP_DAYS:
            raise InvalidRetentionError(self.keep_days, MIN_KEEP_DAYS, MAX_KEEP_DAYS)

    def cutoff(self, now: datetime) -> datetime:
        return now - timedelta(days=self.keep_days)


DEFAULT_RETENTION = RetentionPolicy(keep_days=90)
