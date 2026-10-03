import asyncio
from collections.abc import AsyncIterator, Callable, Iterator
from dataclasses import dataclass, replace
from datetime import UTC, datetime, timedelta
from ipaddress import IPv4Address
from pathlib import Path
from tempfile import TemporaryDirectory

import pytest
from sqlalchemy.ext.asyncio import AsyncEngine

from network_monitor_tds.application.ingestion import ingest
from network_monitor_tds.domain.devices.models import Device
from network_monitor_tds.domain.network.models import MacAddress
from network_monitor_tds.domain.observations.models import (
    Fact,
    KnownField,
    Observation,
    ObservationKind,
)
from network_monitor_tds.domain.plugins.models import PluginId
from network_monitor_tds.infrastructure.db.engine import create_engine, create_session_factory
from network_monitor_tds.infrastructure.db.migrator import upgrade_to_head
from network_monitor_tds.infrastructure.db.unit_of_work import SqlUnitOfWork, unit_of_work_factory
from network_monitor_tds.infrastructure.messaging.bus import InMemoryEventBus
from network_monitor_tds.plugins.sdk.models import PluginInfo
from network_monitor_tds.web.models import WebContext

T0 = datetime(2026, 10, 3, 12, 0, tzinfo=UTC)
NAIVE = datetime(2026, 10, 3, 12, 0)
ARP_SWEEP = PluginId("arp-sweep")
DHCP_SNIFF = PluginId("dhcp-sniff")

type FactsFactory = Callable[[dict[str, str]], dict[str, Fact]]


@pytest.fixture
def mac() -> MacAddress:
    return MacAddress.parse("24:0A:C4:9F:31:5E")


@pytest.fixture
def ip() -> IPv4Address:
    return IPv4Address("192.168.1.143")


@pytest.fixture
def observation(mac: MacAddress, ip: IPv4Address) -> Observation:
    return Observation(
        source=DHCP_SNIFF,
        kind=ObservationKind.SIGHTING,
        mac=mac,
        ip=ip,
        observed_at=T0,
        fields={KnownField.DHCP_HOSTNAME: "esp-31f5e"},
    )


@pytest.fixture
def make_facts() -> FactsFactory:
    def factory(values: dict[str, str]) -> dict[str, Fact]:
        return {
            name: Fact(name=name, value=value, source=DHCP_SNIFF, observed_at=T0)
            for name, value in values.items()
        }

    return factory


@dataclass(frozen=True, slots=True)
class Database:
    path: Path
    engine: AsyncEngine
    unit_of_work: Callable[[], SqlUnitOfWork]


@pytest.fixture
def anyio_backend() -> str:
    return "asyncio"


@pytest.fixture
async def empty_database() -> AsyncIterator[Database]:
    with TemporaryDirectory() as directory:
        path = Path(directory) / "nmtds.db"
        engine = create_engine(path)
        yield Database(
            path=path,
            engine=engine,
            unit_of_work=unit_of_work_factory(create_session_factory(engine)),
        )
        await engine.dispose()


@pytest.fixture
async def database(empty_database: Database) -> Database:
    await upgrade_to_head(empty_database.engine, empty_database.path)
    return empty_database


@pytest.fixture
async def stored_device(database: Database, mac: MacAddress, ip: IPv4Address) -> Device:
    device = Device.discovered(mac, ip, T0)
    async with database.unit_of_work() as uow:
        await uow.devices.save(device)
        await uow.commit()
    return device


class Stop(Exception):  # noqa: N818
    pass


@dataclass(frozen=True, slots=True)
class FixedClock:
    at: datetime

    def now(self) -> datetime:
        return self.at


async def fast_sleep(_seconds: float) -> None:
    await asyncio.sleep(0.001)


async def wait_until(condition: Callable[[], bool]) -> None:
    async with asyncio.timeout(5):
        while not condition():
            await asyncio.sleep(0.005)


@pytest.fixture
def data_dir(monkeypatch: pytest.MonkeyPatch) -> Iterator[Path]:
    with TemporaryDirectory() as directory:
        path = Path(directory) / "data"
        monkeypatch.setenv("NMTDS_DATA_DIR", str(path))
        yield path


DEMO_INFO = PluginInfo(PluginId("demo"), "Demo network", "Simulated devices", False)


@pytest.fixture
def web_context(database: Database) -> WebContext:
    return WebContext(
        unit_of_work=database.unit_of_work,
        events=InMemoryEventBus(10),
        clock=FixedClock(T0 + timedelta(minutes=5)),
        plugins={DEMO_INFO.plugin_id: DEMO_INFO},
        timezone=UTC,
    )


@pytest.fixture
async def seen_device(database: Database, observation: Observation) -> MacAddress:
    await ingest(database.unit_of_work(), replace(observation, source=DEMO_INFO.plugin_id))
    return observation.mac
