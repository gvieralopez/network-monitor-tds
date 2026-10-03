import csv
import gzip
import io
from pathlib import Path

import httpx

REGISTRY_URL = "https://standards-oui.ieee.org/oui/oui.csv"
OUTPUT = Path("src/network_monitor_tds/plugins/builtin/oui/data/oui.tsv.gz")
TIMEOUT_SECONDS = 120


def main() -> None:
    response = httpx.get(
        REGISTRY_URL, headers={"User-Agent": "network-monitor-tds"}, timeout=TIMEOUT_SECONDS
    )
    response.raise_for_status()
    rows = sorted(_prefixes(response.text).items())
    table = "".join(f"{prefix}\t{vendor}\n" for prefix, vendor in rows)
    OUTPUT.write_bytes(gzip.compress(table.encode(), mtime=0))
    print(f"Wrote {len(rows)} prefixes to {OUTPUT}")


def _prefixes(registry: str) -> dict[str, str]:
    return {
        row["Assignment"].lower(): " ".join(row["Organization Name"].split())
        for row in csv.DictReader(io.StringIO(registry))
        if row["Registry"] == "MA-L"
    }


if __name__ == "__main__":
    main()
