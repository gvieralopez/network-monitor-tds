from network_monitor_tds.domain.errors import DomainError


class InvalidMacAddressError(DomainError, ValueError):
    def __init__(self, value: str) -> None:
        super().__init__(f"Not a valid MAC address: {value!r}")
