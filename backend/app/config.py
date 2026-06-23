from functools import lru_cache
from pathlib import Path
import os


class Settings:
    def __init__(self) -> None:
        self.database_path = Path(os.getenv("DATABASE_PATH", "./data/metrics.db"))
        self.host_sys_path = Path(os.getenv("HOST_SYS_PATH", "/sys"))
        self.host_proc_path = Path(os.getenv("HOST_PROC_PATH", "/proc"))
        self.default_collect_interval_seconds = 30
        self.allowed_collect_intervals = {5, 10, 30, 60, 300, 900}


@lru_cache
def get_settings() -> Settings:
    return Settings()
