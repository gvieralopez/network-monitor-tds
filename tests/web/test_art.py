from network_monitor_tds.domain.network.models import MacAddress
from network_monitor_tds.web.art import FillKind, artwork


def test_artwork_is_deterministic(mac: MacAddress) -> None:
    assert artwork(mac) == artwork(mac)


def test_every_pattern_is_used() -> None:
    kinds = set()
    for index in range(64):
        art = artwork(MacAddress.parse(f"02:00:00:00:00:{index:02x}"))
        kinds.add(
            "rings"
            if art.circles
            else "waves"
            if art.strokes
            else art.fill.kind
            if art.fill
            else ""
        )

    assert kinds == {"rings", "waves", FillKind.DOTS, FillKind.STRIPES}


def test_pattern_ids_are_unique_and_safe(mac: MacAddress) -> None:
    other = MacAddress.parse("00:11:32:c4:7e:92")

    assert artwork(mac).pattern_id == "p240ac49f315e"
    assert artwork(mac).pattern_id != artwork(other).pattern_id
