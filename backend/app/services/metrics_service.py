from datetime import datetime, timedelta, timezone
from pathlib import Path
import csv
import io
import json

from ..database import get_connection
from ..models import MetricSnapshot, utc_now_iso


RANGE_TO_DELTA = {
    "1h": timedelta(hours=1),
    "6h": timedelta(hours=6),
    "24h": timedelta(hours=24),
    "7d": timedelta(days=7),
    "30d": timedelta(days=30),
}

CSV_COLUMNS = [
    "timestamp",
    "cpu_percent",
    "temperature_current",
    "temperature_max",
    "power_watts",
    "load_1",
    "load_5",
    "load_15",
    "cpu_freq_current",
    "uptime_seconds",
]


class MetricsService:
    def __init__(self, database_path: Path) -> None:
        self.database_path = database_path

    def save(self, metric: MetricSnapshot) -> None:
        with get_connection(self.database_path) as connection:
            connection.execute(
                """
                INSERT INTO metrics (
                    timestamp, cpu_percent, cpu_per_core_json, cpu_freq_current, cpu_freq_min, cpu_freq_max,
                    load_1, load_5, load_15, temperature_current, temperature_max, temperature_sensors_json,
                    power_watts, energy_joules, uptime_seconds, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    metric.timestamp,
                    metric.cpu_percent,
                    json.dumps(metric.cpu_per_core),
                    metric.cpu_freq.current,
                    metric.cpu_freq.min,
                    metric.cpu_freq.max,
                    metric.load.one,
                    metric.load.five,
                    metric.load.fifteen,
                    metric.temperature.current,
                    metric.temperature.max,
                    json.dumps(metric.temperature.sensors),
                    metric.power.watts,
                    metric.power.energy_joules,
                    metric.uptime_seconds,
                    utc_now_iso(),
                ),
            )
            connection.commit()

    def get_latest(self) -> dict | None:
        with get_connection(self.database_path) as connection:
            row = connection.execute("SELECT * FROM metrics ORDER BY timestamp DESC LIMIT 1").fetchone()
        return self._row_to_api(row) if row else None

    def get_history(self, range_name: str | None = "24h", from_value: str | None = None, to_value: str | None = None) -> list[dict]:
        where_clause, params = self._build_period_filter(range_name, from_value, to_value)
        with get_connection(self.database_path) as connection:
            rows = connection.execute(
                f"SELECT * FROM metrics {where_clause} ORDER BY timestamp ASC",
                params,
            ).fetchall()
        return [self._row_to_api(row) for row in rows]

    def get_summary(self, range_name: str | None = "24h", from_value: str | None = None, to_value: str | None = None) -> dict:
        history = self.get_history(range_name, from_value, to_value)
        return {
            "cpu_percent": self._stats([item["cpu_percent"] for item in history]),
            "temperature": {
                **self._stats([item["temperature"]["current"] for item in history]),
                "available": any(item["temperature"]["available"] for item in history),
            },
            "power": {
                **self._stats([item["power"]["watts"] for item in history]),
                "available": any(item["power"]["available"] for item in history),
            },
        }

    def export_csv(self, range_name: str | None = "24h", from_value: str | None = None, to_value: str | None = None) -> str:
        rows = self.get_history(range_name, from_value, to_value)
        buffer = io.StringIO()
        writer = csv.DictWriter(buffer, fieldnames=CSV_COLUMNS)
        writer.writeheader()
        for item in rows:
            writer.writerow(
                {
                    "timestamp": item["timestamp"],
                    "cpu_percent": item["cpu_percent"],
                    "temperature_current": item["temperature"]["current"],
                    "temperature_max": item["temperature"]["max"],
                    "power_watts": item["power"]["watts"],
                    "load_1": item["load"]["1"],
                    "load_5": item["load"]["5"],
                    "load_15": item["load"]["15"],
                    "cpu_freq_current": item["cpu_freq"]["current"],
                    "uptime_seconds": item["uptime_seconds"],
                }
            )
        return buffer.getvalue()

    def _build_period_filter(self, range_name: str | None, from_value: str | None, to_value: str | None) -> tuple[str, tuple]:
        clauses: list[str] = []
        params: list[str] = []

        if from_value or to_value:
            if from_value:
                clauses.append("timestamp >= ?")
                params.append(from_value)
            if to_value:
                clauses.append("timestamp <= ?")
                params.append(to_value)
        else:
            if range_name not in RANGE_TO_DELTA:
                raise ValueError("range must be one of: 1h, 6h, 24h, 7d, 30d")
            start = datetime.now(timezone.utc) - RANGE_TO_DELTA[range_name or "24h"]
            clauses.append("timestamp >= ?")
            params.append(start.isoformat().replace("+00:00", "Z"))

        if not clauses:
            return "", ()
        return "WHERE " + " AND ".join(clauses), tuple(params)

    def _row_to_api(self, row) -> dict:
        sensors = json.loads(row["temperature_sensors_json"] or "[]")
        cpu_per_core = json.loads(row["cpu_per_core_json"] or "[]")
        return {
            "timestamp": row["timestamp"],
            "cpu_percent": row["cpu_percent"],
            "cpu_per_core": cpu_per_core,
            "cpu_freq": {
                "current": row["cpu_freq_current"],
                "min": row["cpu_freq_min"],
                "max": row["cpu_freq_max"],
            },
            "load": {
                "1": row["load_1"],
                "5": row["load_5"],
                "15": row["load_15"],
            },
            "temperature": {
                "current": row["temperature_current"],
                "max": row["temperature_max"],
                "available": row["temperature_current"] is not None,
                "sensors": sensors,
            },
            "power": {
                "watts": row["power_watts"],
                "energy_joules": row["energy_joules"],
                "available": row["energy_joules"] is not None,
            },
            "uptime_seconds": row["uptime_seconds"],
        }

    def _stats(self, values: list[float | None]) -> dict:
        filtered = [value for value in values if value is not None]
        if not filtered:
            return {"min": None, "avg": None, "max": None}
        return {
            "min": round(min(filtered), 2),
            "avg": round(sum(filtered) / len(filtered), 2),
            "max": round(max(filtered), 2),
        }
