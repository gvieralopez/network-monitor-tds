from dataclasses import replace

import pytest

from network_monitor_tds.domain.errors import NaiveDatetimeError
from network_monitor_tds.domain.observations.models import Fact, Observation
from tests.conftest import DHCP_SNIFF, NAIVE


def test_observation_requires_aware_timestamp(observation: Observation) -> None:
    with pytest.raises(NaiveDatetimeError):
        replace(observation, observed_at=NAIVE)


def test_fact_requires_aware_timestamp() -> None:
    with pytest.raises(NaiveDatetimeError):
        Fact(name="vendor", value="Espressif", source=DHCP_SNIFF, observed_at=NAIVE)
