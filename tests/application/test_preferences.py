from datetime import timedelta

import pytest

from network_monitor_tds.application.preferences import load_presence_policy, save_presence_policy
from network_monitor_tds.domain.presence.policy import DEFAULT_POLICY, PresencePolicy
from tests.conftest import T0, Database

pytestmark = pytest.mark.anyio


async def test_presence_policy_defaults_until_saved(database: Database) -> None:
    assert await load_presence_policy(database.unit_of_work()) == DEFAULT_POLICY


async def test_presence_policy_round_trip(database: Database) -> None:
    policy = PresencePolicy(timedelta(minutes=3), timedelta(minutes=20))

    await save_presence_policy(database.unit_of_work(), policy, T0)
    await save_presence_policy(database.unit_of_work(), policy, T0 + timedelta(minutes=1))

    assert await load_presence_policy(database.unit_of_work()) == policy
