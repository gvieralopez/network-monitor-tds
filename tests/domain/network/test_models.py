import pytest

from network_monitor_tds.domain.network.errors import InvalidMacAddressError
from network_monitor_tds.domain.network.models import MacAddress


@pytest.mark.parametrize(
    "raw",
    [
        "24:0a:c4:9f:31:5e",
        "24:0A:C4:9F:31:5E",
        "24-0A-C4-9F-31-5E",
        "240a.c49f.315e",
        "240AC49F315E",
        "  24:0a:c4:9f:31:5e\n",
    ],
)
def test_parse_normalises_formats(raw: str) -> None:
    assert MacAddress.parse(raw).value == "24:0a:c4:9f:31:5e"


@pytest.mark.parametrize("raw", ["", "24:0a:c4:9f:31", "24:0a:c4:9f:31:5e:00", "zz:0a:c4:9f:31:5e"])
def test_parse_rejects_invalid_input(raw: str) -> None:
    with pytest.raises(InvalidMacAddressError):
        MacAddress.parse(raw)


@pytest.mark.parametrize("value", ["24:0A:C4:9F:31:5E", "240ac49f315e", "24-0a-c4-9f-31-5e"])
def test_constructor_requires_canonical_form(value: str) -> None:
    with pytest.raises(InvalidMacAddressError):
        MacAddress(value)


@pytest.mark.parametrize(
    ("raw", "randomized"),
    [
        ("24:0a:c4:9f:31:5e", False),
        ("a6:3e:91:0c:58:f7", True),
        ("3a:f1:5c:22:9b:07", True),
        ("00:11:32:c4:7e:92", False),
    ],
)
def test_is_randomized_reads_locally_administered_bit(raw: str, randomized: bool) -> None:
    assert MacAddress.parse(raw).is_randomized is randomized


@pytest.mark.parametrize(
    ("raw", "multicast"),
    [("01:00:5e:00:00:fb", True), ("ff:ff:ff:ff:ff:ff", True), ("24:0a:c4:9f:31:5e", False)],
)
def test_is_multicast_reads_group_bit(raw: str, multicast: bool) -> None:
    assert MacAddress.parse(raw).is_multicast is multicast


def test_oui_and_str(mac: MacAddress) -> None:
    assert mac.oui == "24:0a:c4"
    assert str(mac) == "24:0a:c4:9f:31:5e"
