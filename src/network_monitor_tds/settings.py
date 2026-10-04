from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

DATABASE_FILENAME = "nmtds.db"


class AppSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="NMTDS_", frozen=True)

    data_dir: Path = Path("data")
    host: str = "127.0.0.1"
    port: int = 8000
    observation_queue_size: int = 1000
    event_queue_size: int = 100

    @property
    def database_path(self) -> Path:
        return self.data_dir / DATABASE_FILENAME
