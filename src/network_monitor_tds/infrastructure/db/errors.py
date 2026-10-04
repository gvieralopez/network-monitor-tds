from network_monitor_tds.errors import NetworkMonitorError


class DatabaseError(NetworkMonitorError):
    pass


class UnknownSchemaRevisionError(DatabaseError):
    def __init__(self, revision: str) -> None:
        super().__init__(
            f"The database is at schema revision {revision!r}, which this version does not know. "
            "It was probably created by a newer release; upgrade the application or restore a "
            "backup."
        )
