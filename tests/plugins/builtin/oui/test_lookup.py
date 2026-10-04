import pytest

from network_monitor_tds.domain.network.models import MacAddress
from network_monitor_tds.plugins.builtin.oui.lookup import (
    clean_vendor,
    vendor_directory,
    vendor_for,
)


@pytest.mark.parametrize(
    ("mac", "vendor"),
    [
        ("24:0a:c4:9f:31:5e", "Espressif"),
        ("dc:a6:32:58:a0:3f", "Raspberry Pi Trading"),
        ("00:11:32:c4:7e:92", "Synology"),
        ("fe:ff:ff:00:00:01", None),
    ],
)
def test_vendor_for(mac: str, vendor: str | None) -> None:
    assert vendor_for(MacAddress.parse(mac)) == vendor


def test_directory_is_large_and_cached() -> None:
    assert len(vendor_directory()) > 30_000
    assert vendor_directory() is vendor_directory()


@pytest.mark.parametrize(
    ("raw", "clean"),
    [
        ("Espressif Inc.", "Espressif"),
        ("TP-LINK TECHNOLOGIES CO.,LTD.", "TP-LINK TECHNOLOGIES"),
        ("CLOUD NETWORK TECHNOLOGY SINGAPORE PTE. LTD.", "CLOUD NETWORK TECHNOLOGY SINGAPORE"),
        ("ASRock Incorporation", "ASRock"),
        ("Apple, Inc.", "Apple"),
        ("Ltd", "Ltd"),
        ("Google", "Google"),
    ],
)
def test_clean_vendor(raw: str, clean: str) -> None:
    assert clean_vendor(raw) == clean
