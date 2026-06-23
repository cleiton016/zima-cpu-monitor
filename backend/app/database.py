from pathlib import Path
import sqlite3


METRICS_SCHEMA = """
CREATE TABLE IF NOT EXISTS metrics (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  timestamp TEXT NOT NULL,
  cpu_percent REAL,
  cpu_per_core_json TEXT,
  cpu_freq_current REAL,
  cpu_freq_min REAL,
  cpu_freq_max REAL,
  load_1 REAL,
  load_5 REAL,
  load_15 REAL,
  temperature_current REAL,
  temperature_max REAL,
  temperature_sensors_json TEXT,
  power_watts REAL,
  energy_joules REAL,
  uptime_seconds INTEGER,
  created_at TEXT NOT NULL
);
"""

SETTINGS_SCHEMA = """
CREATE TABLE IF NOT EXISTS settings (
  key TEXT PRIMARY KEY,
  value TEXT NOT NULL,
  updated_at TEXT NOT NULL
);
"""

APP_SETTINGS_SCHEMA = """
CREATE TABLE IF NOT EXISTS app_settings (
  key TEXT PRIMARY KEY,
  value TEXT NOT NULL,
  updated_at TEXT NOT NULL
);
"""

RAM_SAMPLES_SCHEMA = """
CREATE TABLE IF NOT EXISTS ram_samples (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  timestamp TEXT NOT NULL,
  total_bytes INTEGER NOT NULL,
  used_bytes INTEGER NOT NULL,
  available_bytes INTEGER NOT NULL,
  free_bytes INTEGER,
  usage_percent REAL NOT NULL,
  buffers_bytes INTEGER,
  cached_bytes INTEGER,
  shared_bytes INTEGER,
  swap_total_bytes INTEGER,
  swap_used_bytes INTEGER,
  swap_usage_percent REAL,
  temperature_celsius REAL,
  created_at TEXT NOT NULL
);
"""

PROCESS_MEMORY_SAMPLES_SCHEMA = """
CREATE TABLE IF NOT EXISTS process_memory_samples (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  timestamp TEXT NOT NULL,
  pid INTEGER NOT NULL,
  name TEXT,
  command TEXT,
  memory_bytes INTEGER,
  memory_percent REAL,
  created_at TEXT NOT NULL
);
"""

STORAGE_SAMPLES_SCHEMA = """
CREATE TABLE IF NOT EXISTS storage_samples (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  timestamp TEXT NOT NULL,
  device_name TEXT NOT NULL,
  model TEXT,
  type TEXT,
  size_bytes INTEGER,
  used_bytes INTEGER,
  free_bytes INTEGER,
  usage_percent REAL,
  temperature_celsius REAL,
  smart_status TEXT,
  read_bytes_total INTEGER,
  write_bytes_total INTEGER,
  read_bytes_per_second REAL,
  write_bytes_per_second REAL,
  created_at TEXT NOT NULL
);
"""

STORAGE_MOUNT_SAMPLES_SCHEMA = """
CREATE TABLE IF NOT EXISTS storage_mount_samples (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  timestamp TEXT NOT NULL,
  device TEXT,
  mount_point TEXT NOT NULL,
  filesystem TEXT,
  total_bytes INTEGER,
  used_bytes INTEGER,
  free_bytes INTEGER,
  usage_percent REAL,
  created_at TEXT NOT NULL
);
"""

GPU_SAMPLES_SCHEMA = """
CREATE TABLE IF NOT EXISTS gpu_samples (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  timestamp TEXT NOT NULL,
  gpu_id TEXT NOT NULL,
  vendor TEXT,
  model TEXT,
  usage_percent REAL,
  temperature_celsius REAL,
  memory_total_bytes INTEGER,
  memory_used_bytes INTEGER,
  memory_usage_percent REAL,
  power_watts REAL,
  source TEXT,
  created_at TEXT NOT NULL
);
"""

ENERGY_SAMPLES_SCHEMA = """
CREATE TABLE IF NOT EXISTS energy_samples (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  timestamp TEXT NOT NULL,
  power_watts REAL,
  energy_kwh REAL,
  source TEXT NOT NULL,
  created_at TEXT NOT NULL
);
"""


def get_connection(database_path: Path) -> sqlite3.Connection:
    database_path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(database_path)
    connection.row_factory = sqlite3.Row
    return connection


def initialize_database(database_path: Path, default_interval: int) -> None:
    with get_connection(database_path) as connection:
        connection.execute(METRICS_SCHEMA)
        connection.execute(SETTINGS_SCHEMA)
        connection.execute(APP_SETTINGS_SCHEMA)
        connection.execute(RAM_SAMPLES_SCHEMA)
        connection.execute(PROCESS_MEMORY_SAMPLES_SCHEMA)
        connection.execute(STORAGE_SAMPLES_SCHEMA)
        connection.execute(STORAGE_MOUNT_SAMPLES_SCHEMA)
        connection.execute(GPU_SAMPLES_SCHEMA)
        connection.execute(ENERGY_SAMPLES_SCHEMA)
        connection.execute(
            """
            INSERT OR IGNORE INTO settings (key, value, updated_at)
            VALUES ('collect_interval_seconds', ?, datetime('now'))
            """,
            (str(default_interval),),
        )
        connection.commit()
