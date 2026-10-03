from datetime import datetime, timedelta

from network_monitor_tds.domain.network.models import MacAddress


class Throttle:
    def __init__(self, window: timedelta) -> None:
        self._window = window
        self._last: dict[MacAddress, datetime] = {}

    def allow(self, mac: MacAddress, now: datetime) -> bool:
        last = self._last.get(mac)
        if last is not None and now - last < self._window:
            return False
        self._last[mac] = now
        return True
