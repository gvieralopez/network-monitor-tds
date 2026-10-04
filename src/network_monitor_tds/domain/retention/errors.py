from network_monitor_tds.domain.errors import DomainError


class InvalidRetentionError(DomainError, ValueError):
    def __init__(self, keep_days: int, minimum: int, maximum: int) -> None:
        super().__init__(f"History must be kept for {minimum} to {maximum} days, got {keep_days}")
