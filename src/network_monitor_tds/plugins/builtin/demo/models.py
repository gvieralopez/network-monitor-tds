from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import StrEnum
from ipaddress import IPv4Address

from network_monitor_tds.domain.network.models import MacAddress

WORK_HOURS = range(8, 18)
EVENING_HOURS = range(18, 24)
SATURDAY = 5


class Routine(StrEnum):
    ALWAYS = "always"
    WORKDAY = "workday"
    EVENING = "evening"
    PHONE = "phone"
    SPORADIC = "sporadic"


@dataclass(frozen=True, slots=True)
class DemoDevice:
    mac: MacAddress
    ip: IPv4Address
    routine: Routine
    appears_after: timedelta
    fields: dict[str, str]

    def is_online(self, now: datetime, running_for: timedelta) -> bool:
        if running_for < self.appears_after:
            return False
        local = now.astimezone()
        weekend = local.weekday() >= SATURDAY
        match self.routine:
            case Routine.ALWAYS:
                return True
            case Routine.WORKDAY:
                return not weekend and local.hour in WORK_HOURS
            case Routine.EVENING:
                return local.hour in EVENING_HOURS
            case Routine.PHONE:
                return weekend or local.hour not in WORK_HOURS
            case Routine.SPORADIC:
                return (local.toordinal() * 24 + local.hour + int(self.ip)) % 4 == 0
