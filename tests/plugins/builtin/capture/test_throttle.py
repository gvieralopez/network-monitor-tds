from datetime import timedelta

from network_monitor_tds.domain.network.models import MacAddress
from network_monitor_tds.plugins.builtin.capture.throttle import Throttle
from tests.conftest import T0

OTHER = MacAddress.parse("00:11:32:c4:7e:92")


def test_throttle_allows_once_per_window(mac: MacAddress) -> None:
    throttle = Throttle(timedelta(minutes=1))

    assert throttle.allow(mac, T0) is True
    assert throttle.allow(mac, T0 + timedelta(seconds=59)) is False
    assert throttle.allow(OTHER, T0 + timedelta(seconds=59)) is True
    assert throttle.allow(mac, T0 + timedelta(minutes=1)) is True
