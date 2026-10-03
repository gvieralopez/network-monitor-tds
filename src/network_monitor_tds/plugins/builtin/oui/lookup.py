import gzip
from functools import cache
from pathlib import Path

from network_monitor_tds.domain.network.models import MacAddress

DATA_FILE = Path(__file__).parent / "data" / "oui.tsv.gz"
LEGAL_SUFFIXES = frozenset(
    {
        "ab", "ag", "as", "bv", "co", "company", "corp", "corporation", "gmbh", "inc",
        "incorporated", "incorporation", "kg", "limited", "llc", "ltd", "oy", "plc", "pte", "pty", "sa", "sas",
        "spa", "srl",
    }
)  # fmt: skip


def vendor_for(mac: MacAddress) -> str | None:
    vendor = vendor_directory().get(mac.oui.replace(":", ""))
    return clean_vendor(vendor) if vendor is not None else None


@cache
def vendor_directory() -> dict[str, str]:
    table = gzip.decompress(DATA_FILE.read_bytes()).decode()
    return dict(line.split("\t", 1) for line in table.splitlines())


def clean_vendor(name: str) -> str:
    words = name.replace(",", " ").split()
    while len(words) > 1 and _is_legal_suffix(words[-1]):
        words.pop()
    return " ".join(words)


def _is_legal_suffix(word: str) -> bool:
    return word.lower().replace(".", "") in LEGAL_SUFFIXES
