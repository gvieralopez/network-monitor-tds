import re
from dataclasses import dataclass
from typing import Self

from network_monitor_tds.domain.network.errors import InvalidMacAddressError

_CANONICAL = re.compile(r"(?:[0-9a-f]{2}:){5}[0-9a-f]{2}")
_HEX_DIGITS = re.compile(r"[0-9a-f]{12}")
_SEPARATORS = str.maketrans("", "", ":-.")


@dataclass(frozen=True, slots=True)
class MacAddress:
    value: str

    def __post_init__(self) -> None:
        if not _CANONICAL.fullmatch(self.value):
            raise InvalidMacAddressError(self.value)

    @classmethod
    def parse(cls, raw: str) -> Self:
        digits = raw.strip().lower().translate(_SEPARATORS)
        if not _HEX_DIGITS.fullmatch(digits):
            raise InvalidMacAddressError(raw)
        return cls(":".join(digits[i : i + 2] for i in range(0, 12, 2)))

    @property
    def is_randomized(self) -> bool:
        return bool(self._first_octet & 0b10)

    @property
    def is_multicast(self) -> bool:
        return bool(self._first_octet & 0b01)

    @property
    def oui(self) -> str:
        return self.value[:8]

    def __str__(self) -> str:
        return self.value

    @property
    def _first_octet(self) -> int:
        return int(self.value[:2], 16)
