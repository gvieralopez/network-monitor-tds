from datetime import datetime, timedelta

import pytest

from network_monitor_tds.domain.observations.detections import record_detection
from network_monitor_tds.domain.observations.models import Detection
from tests.conftest import ARP_SWEEP, T0

M = timedelta(minutes=1)


def test_first_detection() -> None:
    assert record_detection(None, ARP_SWEEP, T0) == Detection(ARP_SWEEP, T0, T0)


@pytest.mark.parametrize(
    ("at", "expected"),
    [
        (T0 + 10 * M, Detection(ARP_SWEEP, T0, T0 + 10 * M)),
        (T0 - 10 * M, Detection(ARP_SWEEP, T0 - 10 * M, T0 + 5 * M)),
        (T0 + 2 * M, Detection(ARP_SWEEP, T0, T0 + 5 * M)),
    ],
)
def test_detection_widens_to_cover_sighting(at: datetime, expected: Detection) -> None:
    current = Detection(ARP_SWEEP, T0, T0 + 5 * M)

    assert record_detection(current, ARP_SWEEP, at) == expected
