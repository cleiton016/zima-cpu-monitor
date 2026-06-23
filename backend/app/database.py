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


def get_connection(database_path: Path) -> sqlite3.Connection:
    database_path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(database_path)
    connection.row_factory = sqlite3.Row
    return connection


def initialize_database(database_path: Path, default_interval: int) -> None:
    with get_connection(database_path) as connection:
        connection.execute(METRICS_SCHEMA)
        connection.execute(SETTINGS_SCHEMA)
        connection.execute(
            """
            INSERT OR IGNORE INTO settings (key, value, updated_at)
            VALUES ('collect_interval_seconds', ?, datetime('now'))
            """,
            (str(default_interval),),
        )
        connection.commit()
