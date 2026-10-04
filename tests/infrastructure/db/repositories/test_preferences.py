from datetime import timedelta

import pytest

from tests.conftest import T0, Database

pytestmark = pytest.mark.anyio


async def test_preferences_round_trip(database: Database) -> None:
    async with database.unit_of_work() as uow:
        assert await uow.preferences.get("presence") is None
        await uow.preferences.save("presence", {"offline_after_seconds": 600}, T0)
        await uow.preferences.save(
            "presence", {"offline_after_seconds": 300}, T0 + timedelta(hours=1)
        )
        await uow.commit()

    async with database.unit_of_work() as uow:
        assert await uow.preferences.get("presence") == {"offline_after_seconds": 300}
