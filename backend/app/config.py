from functools import lru_cache
from pathlib import Path
import os


class Settings:
    def __init__(self) -> None:
        self.database_path = Path(os.getenv("DATABASE_PATH", "./data/metrics.db"))
        self.host_sys_path = Path(os.getenv("HOST_SYS_PATH", "/sys"))
        self.host_proc_path = Path(os.getenv("HOST_PROC_PATH", "/proc"))
        self.allowed_collect_intervals = {5, 10, 30, 60, 300, 900}
        self.default_collect_interval_seconds = self._read_collect_interval()

    def _read_collect_interval(self) -> int:
        try:
            interval = int(os.getenv("COLLECT_INTERVAL_SECONDS", "30"))
        except ValueError:
            return 30
        return interval if interval in self.allowed_collect_intervals else 30


@lru_cache
def get_settings() -> Settings:
    return Settings()
