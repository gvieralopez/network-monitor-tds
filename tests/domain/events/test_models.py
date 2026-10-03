import pytest

from network_monitor_tds.domain.errors import NaiveDatetimeError
from network_monitor_tds.domain.events.models import DeviceEvent, EventKind
from network_monitor_tds.domain.network.models import MacAddress
from tests.conftest import NAIVE


def test_event_requires_aware_timestamp(mac: MacAddress) -> None:
    with pytest.raises(NaiveDatetimeError):
        DeviceEvent(EventKind.DEVICE_ONLINE, mac, NAIVE)
