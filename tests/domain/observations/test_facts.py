from dataclasses import replace
from datetime import timedelta

import pytest

from network_monitor_tds.domain.observations.facts import merge_facts
from network_monitor_tds.domain.observations.models import Fact, KnownField, Observation
from tests.conftest import ARP_SWEEP, DHCP_SNIFF, T0


def test_merge_into_empty_creates_facts(observation: Observation) -> None:
    facts = merge_facts({}, observation)

    assert facts == {
        KnownField.DHCP_HOSTNAME: Fact(
            name=KnownField.DHCP_HOSTNAME, value="esp-31f5e", source=DHCP_SNIFF, observed_at=T0
        )
    }


@pytest.mark.parametrize(
    ("offset", "expected"),
    [(timedelta(minutes=1), "new-name"), (timedelta(minutes=-1), "old-name")],
)
def test_newest_value_wins(observation: Observation, offset: timedelta, expected: str) -> None:
    current: dict[str, Fact] = {
        KnownField.DHCP_HOSTNAME: Fact(
            name=KnownField.DHCP_HOSTNAME, value="old-name", source=ARP_SWEEP, observed_at=T0
        )
    }
    update = replace(
        observation, observed_at=T0 + offset, fields={KnownField.DHCP_HOSTNAME: "new-name"}
    )

    assert merge_facts(current, update)[KnownField.DHCP_HOSTNAME].value == expected


@pytest.mark.parametrize("value", ["", "   ", "\t\n"])
def test_blank_values_are_ignored(observation: Observation, value: str) -> None:
    assert merge_facts({}, replace(observation, fields={KnownField.VENDOR: value})) == {}


def test_values_are_stripped(observation: Observation) -> None:
    facts = merge_facts({}, replace(observation, fields={KnownField.VENDOR: "  Espressif \n"}))

    assert facts[KnownField.VENDOR].value == "Espressif"


def test_merge_does_not_mutate_input(observation: Observation) -> None:
    current: dict[str, Fact] = {}

    merge_facts(current, observation)

    assert current == {}
