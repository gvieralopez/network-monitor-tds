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
    vendor = _find_vendor(vendor_directory(), mac.oui.replace(":", ""))
    return clean_vendor(vendor) if vendor is not None else None


# Kept as the raw "<prefix>\t<vendor>\n" lines (about 1 MiB) rather than a dict of 40 000
# entries (about 8 MiB), since lookups only happen when a device is first seen.
@cache
def vendor_directory() -> bytes:
    return b"\n" + gzip.decompress(DATA_FILE.read_bytes())


def clean_vendor(name: str) -> str:
    words = name.replace(",", " ").split()
    while len(words) > 1 and _is_legal_suffix(words[-1]):
        words.pop()
    return " ".join(words)


def _is_legal_suffix(word: str) -> bool:
    return word.lower().replace(".", "") in LEGAL_SUFFIXES


def _find_vendor(directory: bytes, prefix: str) -> str | None:
    key = f"\n{prefix}\t".encode()
    start = directory.find(key)
    if start < 0:
        return None
    start += len(key)
    end = directory.find(b"\n", start)
    return directory[start : end if end >= 0 else len(directory)].decode()
