from collections.abc import Mapping

from network_monitor_tds.domain.devices.classification import classify
from network_monitor_tds.domain.devices.models import Category, DeviceLabels, Fallback, Resolved
from network_monitor_tds.domain.network.models import MacAddress
from network_monitor_tds.domain.observations.models import Fact, KnownField

NAME_PRIORITY = (
    KnownField.LEASE_HOSTNAME,
    KnownField.DHCP_HOSTNAME,
    KnownField.MDNS_NAME,
    KnownField.UPNP_FRIENDLY_NAME,
)
_PLACEHOLDER_NAMES = frozenset({"*", "localhost", "unknown", "none", "(none)"})
_LOCAL_SUFFIXES = (".local", ".lan", ".home", ".localdomain", ".home.arpa")


def resolve_name(mac: MacAddress, labels: DeviceLabels, facts: Mapping[str, Fact]) -> Resolved[str]:
    if labels.name is not None:
        return Resolved(labels.name.strip(), Fallback.USER)
    for field in NAME_PRIORITY:
        fact = facts.get(field)
        name = _clean_hostname(fact.value) if fact is not None else ""
        if name:
            return Resolved(name, field)
    vendor = facts.get(KnownField.VENDOR)
    if vendor is not None:
        return Resolved(f"{vendor.value} device", KnownField.VENDOR)
    return Resolved(str(mac), Fallback.MAC_ADDRESS)


def resolve_category(labels: DeviceLabels, facts: Mapping[str, Fact]) -> Resolved[Category]:
    if labels.category is not None:
        return Resolved(labels.category, Fallback.USER)
    return classify(facts)


def _clean_hostname(raw: str) -> str:
    name = raw.strip().rstrip(".")
    for suffix in _LOCAL_SUFFIXES:
        name = name.removesuffix(suffix)
    return "" if name.lower() in _PLACEHOLDER_NAMES else name
