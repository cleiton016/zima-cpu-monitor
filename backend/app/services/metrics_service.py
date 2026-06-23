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

    def save_ram_sample(self, sample: dict) -> None:
        with get_connection(self.database_path) as connection:
            connection.execute(
                """
                INSERT INTO ram_samples (
                    timestamp, total_bytes, used_bytes, available_bytes, free_bytes, usage_percent,
                    buffers_bytes, cached_bytes, shared_bytes, swap_total_bytes, swap_used_bytes,
                    swap_usage_percent, temperature_celsius, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    sample["timestamp"],
                    sample["totalBytes"],
                    sample["usedBytes"],
                    sample["availableBytes"],
                    sample.get("freeBytes"),
                    sample["usagePercent"],
                    sample.get("buffersBytes"),
                    sample.get("cachedBytes"),
                    sample.get("sharedBytes"),
                    sample.get("swapTotalBytes"),
                    sample.get("swapUsedBytes"),
                    sample.get("swapUsagePercent"),
                    sample.get("temperatureCelsius"),
                    utc_now_iso(),
                ),
            )
            connection.commit()

    def save_process_memory_samples(self, sample: dict) -> None:
        with get_connection(self.database_path) as connection:
            connection.executemany(
                """
                INSERT INTO process_memory_samples (
                    timestamp, pid, name, command, memory_bytes, memory_percent, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                [
                    (
                        sample["timestamp"],
                        process["pid"],
                        process.get("name"),
                        process.get("command"),
                        process.get("memoryBytes"),
                        process.get("memoryPercent"),
                        utc_now_iso(),
                    )
                    for process in sample.get("processes", [])
                    if process.get("pid") is not None
                ],
            )
            connection.commit()

    def save_storage_current(self, sample: dict) -> None:
        mounts_by_device = {}
        for mount in sample.get("mounts", []):
            device_name = str(mount.get("device") or "").split("/")[-1]
            if device_name:
                mounts_by_device[device_name] = mount

        with get_connection(self.database_path) as connection:
            connection.executemany(
                """
                INSERT INTO storage_samples (
                    timestamp, device_name, model, type, size_bytes, used_bytes, free_bytes,
                    usage_percent, temperature_celsius, smart_status, read_bytes_total,
                    write_bytes_total, read_bytes_per_second, write_bytes_per_second, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                [
                    (
                        sample["timestamp"],
                        device["name"],
                        device.get("model"),
                        device.get("type"),
                        device.get("sizeBytes"),
                        self._storage_mount_for_device(device["name"], mounts_by_device).get("usedBytes"),
                        self._storage_mount_for_device(device["name"], mounts_by_device).get("freeBytes"),
                        self._storage_mount_for_device(device["name"], mounts_by_device).get("usagePercent"),
                        device.get("temperatureCelsius"),
                        device.get("smartStatus"),
                        device.get("readBytesTotal"),
                        device.get("writeBytesTotal"),
                        device.get("readBytesPerSecond"),
                        device.get("writeBytesPerSecond"),
                        utc_now_iso(),
                    )
                    for device in sample.get("devices", [])
                ],
            )
            connection.executemany(
                """
                INSERT INTO storage_mount_samples (
                    timestamp, device, mount_point, filesystem, total_bytes, used_bytes,
                    free_bytes, usage_percent, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                [
                    (
                        sample["timestamp"],
                        mount.get("device"),
                        mount["mountPoint"],
                        mount.get("filesystem"),
                        mount.get("totalBytes"),
                        mount.get("usedBytes"),
                        mount.get("freeBytes"),
                        mount.get("usagePercent"),
                        utc_now_iso(),
                    )
                    for mount in sample.get("mounts", [])
                ],
            )
            connection.commit()

    def save_gpu_current(self, sample: dict) -> None:
        with get_connection(self.database_path) as connection:
            connection.executemany(
                """
                INSERT INTO gpu_samples (
                    timestamp, gpu_id, vendor, model, usage_percent, temperature_celsius,
                    memory_total_bytes, memory_used_bytes, memory_usage_percent, power_watts,
                    source, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                [
                    (
                        sample["timestamp"],
                        device["id"],
                        device.get("vendor"),
                        device.get("model"),
                        device.get("usagePercent"),
                        device.get("temperatureCelsius"),
                        device.get("memoryTotalBytes"),
                        device.get("memoryUsedBytes"),
                        device.get("memoryUsagePercent"),
                        device.get("powerWatts"),
                        "sysfs",
                        utc_now_iso(),
                    )
                    for device in sample.get("devices", [])
                ],
            )
            connection.commit()

    def save_energy_sample(self, timestamp: str, power_watts: float | None, energy_kwh: float | None, source: str) -> None:
        if power_watts is None and energy_kwh is None:
            return
        with get_connection(self.database_path) as connection:
            connection.execute(
                """
                INSERT INTO energy_samples (timestamp, power_watts, energy_kwh, source, created_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                (timestamp, power_watts, energy_kwh, source, utc_now_iso()),
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

    def get_daily_summary(self, date_value: str | None = None) -> dict:
        date_string = date_value or datetime.now(timezone.utc).date().isoformat()
        start = f"{date_string}T00:00:00"
        end = f"{date_string}T23:59:59"

        with get_connection(self.database_path) as connection:
            cpu_peak = connection.execute(
                """
                SELECT cpu_percent AS value, timestamp FROM metrics
                WHERE timestamp >= ? AND timestamp <= ? AND cpu_percent IS NOT NULL
                ORDER BY cpu_percent DESC LIMIT 1
                """,
                (start, end),
            ).fetchone()
            temperature_peak = connection.execute(
                """
                SELECT temperature_current AS value, timestamp FROM metrics
                WHERE timestamp >= ? AND timestamp <= ? AND temperature_current IS NOT NULL
                ORDER BY temperature_current DESC LIMIT 1
                """,
                (start, end),
            ).fetchone()
            ram_peak = connection.execute(
                """
                SELECT usage_percent AS value, timestamp FROM ram_samples
                WHERE timestamp >= ? AND timestamp <= ? AND usage_percent IS NOT NULL
                ORDER BY usage_percent DESC LIMIT 1
                """,
                (start, end),
            ).fetchone()
            energy_total = connection.execute(
                """
                SELECT COALESCE(SUM(energy_kwh), 0) AS kwh FROM energy_samples
                WHERE timestamp >= ? AND timestamp <= ?
                """,
                (start, end),
            ).fetchone()
            settings_rows = connection.execute(
                "SELECT key, value FROM app_settings WHERE key IN ('energy.kwh_price', 'energy.currency')"
            ).fetchall()

        settings = {row["key"]: row["value"] for row in settings_rows}
        kwh_price = float(settings.get("energy.kwh_price", 0.95))
        currency = settings.get("energy.currency", "BRL")
        kwh = round(float(energy_total["kwh"] or 0), 4) if energy_total else 0
        return {
            "date": date_string,
            "cpuPeak": self._peak(cpu_peak, "valuePercent"),
            "temperaturePeak": self._peak(temperature_peak, "valueCelsius"),
            "ramPeak": self._peak(ram_peak, "valuePercent"),
            "energyTotal": {
                "kwh": kwh,
                "estimatedCost": round(kwh * kwh_price, 2) if kwh else None,
                "currency": currency,
            },
        }

    def get_ram_history(self, from_value: str | None = None, to_value: str | None = None) -> list[dict]:
        where_clause, params = self._build_optional_filter(from_value, to_value)
        with get_connection(self.database_path) as connection:
            rows = connection.execute(f"SELECT * FROM ram_samples {where_clause} ORDER BY timestamp ASC", params).fetchall()
        return [self._ram_row_to_api(row) for row in rows]

    def get_storage_history(self, device: str | None = None, from_value: str | None = None, to_value: str | None = None) -> list[dict]:
        where_clause, params = self._build_optional_filter(from_value, to_value)
        clauses = []
        query_params = list(params)
        if where_clause:
            clauses.append(where_clause.replace("WHERE ", ""))
        if device:
            clauses.append("device_name = ?")
            query_params.append(device)
        final_where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
        with get_connection(self.database_path) as connection:
            rows = connection.execute(f"SELECT * FROM storage_samples {final_where} ORDER BY timestamp ASC", tuple(query_params)).fetchall()
        return [self._storage_row_to_api(row) for row in rows]

    def get_gpu_history(self, from_value: str | None = None, to_value: str | None = None) -> list[dict]:
        where_clause, params = self._build_optional_filter(from_value, to_value)
        with get_connection(self.database_path) as connection:
            rows = connection.execute(f"SELECT * FROM gpu_samples {where_clause} ORDER BY timestamp ASC", params).fetchall()
        return [self._gpu_row_to_api(row) for row in rows]

    def get_energy_history(self, from_value: str | None = None, to_value: str | None = None) -> list[dict]:
        where_clause, params = self._build_optional_filter(from_value, to_value)
        with get_connection(self.database_path) as connection:
            rows = connection.execute(f"SELECT * FROM energy_samples {where_clause} ORDER BY timestamp ASC", params).fetchall()
        return [self._energy_row_to_api(row) for row in rows]

    def get_energy_monthly(self, year: int | None = None) -> dict:
        selected_year = year or datetime.now(timezone.utc).year
        with get_connection(self.database_path) as connection:
            rows = connection.execute(
                """
                SELECT CAST(strftime('%m', timestamp) AS INTEGER) AS month, COALESCE(SUM(energy_kwh), 0) AS kwh
                FROM energy_samples
                WHERE strftime('%Y', timestamp) = ?
                GROUP BY month
                """,
                (str(selected_year),),
            ).fetchall()
            settings_rows = connection.execute(
                "SELECT key, value FROM app_settings WHERE key IN ('energy.kwh_price', 'energy.currency')"
            ).fetchall()

        settings = {row["key"]: row["value"] for row in settings_rows}
        kwh_price = float(settings.get("energy.kwh_price", 0.95))
        currency = settings.get("energy.currency", "BRL")
        by_month = {row["month"]: float(row["kwh"] or 0) for row in rows}
        labels = ["Jan", "Fev", "Mar", "Abr", "Mai", "Jun", "Jul", "Ago", "Set", "Out", "Nov", "Dez"]
        return {
            "year": selected_year,
            "currency": currency,
            "kwhPrice": kwh_price,
            "months": [
                {
                    "month": month,
                    "label": labels[month - 1],
                    "kwh": round(by_month.get(month, 0), 4),
                    "cost": round(by_month.get(month, 0) * kwh_price, 2),
                }
                for month in range(1, 13)
            ],
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

    def _build_optional_filter(self, from_value: str | None, to_value: str | None) -> tuple[str, tuple]:
        clauses: list[str] = []
        params: list[str] = []
        if from_value:
            clauses.append("timestamp >= ?")
            params.append(from_value)
        if to_value:
            clauses.append("timestamp <= ?")
            params.append(to_value)
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

    def _peak(self, row, value_key: str) -> dict:
        return {
            value_key: row["value"] if row else None,
            "timestamp": row["timestamp"] if row else None,
        }

    def _ram_row_to_api(self, row) -> dict:
        return {
            "timestamp": row["timestamp"],
            "totalBytes": row["total_bytes"],
            "usedBytes": row["used_bytes"],
            "availableBytes": row["available_bytes"],
            "freeBytes": row["free_bytes"],
            "usagePercent": row["usage_percent"],
            "buffersBytes": row["buffers_bytes"],
            "cachedBytes": row["cached_bytes"],
            "sharedBytes": row["shared_bytes"],
            "swapTotalBytes": row["swap_total_bytes"],
            "swapUsedBytes": row["swap_used_bytes"],
            "swapUsagePercent": row["swap_usage_percent"],
            "temperatureCelsius": row["temperature_celsius"],
        }

    def _storage_row_to_api(self, row) -> dict:
        return {
            "timestamp": row["timestamp"],
            "name": row["device_name"],
            "model": row["model"],
            "type": row["type"],
            "sizeBytes": row["size_bytes"],
            "usedBytes": row["used_bytes"],
            "freeBytes": row["free_bytes"],
            "usagePercent": row["usage_percent"],
            "temperatureCelsius": row["temperature_celsius"],
            "smartStatus": row["smart_status"],
            "readBytesTotal": row["read_bytes_total"],
            "writeBytesTotal": row["write_bytes_total"],
            "readBytesPerSecond": row["read_bytes_per_second"],
            "writeBytesPerSecond": row["write_bytes_per_second"],
        }

    def _gpu_row_to_api(self, row) -> dict:
        return {
            "timestamp": row["timestamp"],
            "id": row["gpu_id"],
            "vendor": row["vendor"],
            "model": row["model"],
            "usagePercent": row["usage_percent"],
            "temperatureCelsius": row["temperature_celsius"],
            "memoryTotalBytes": row["memory_total_bytes"],
            "memoryUsedBytes": row["memory_used_bytes"],
            "memoryUsagePercent": row["memory_usage_percent"],
            "powerWatts": row["power_watts"],
            "source": row["source"],
        }

    def _energy_row_to_api(self, row) -> dict:
        return {
            "timestamp": row["timestamp"],
            "powerWatts": row["power_watts"],
            "energyKwh": row["energy_kwh"],
            "source": row["source"],
        }

    def _storage_mount_for_device(self, device_name: str, mounts_by_device: dict) -> dict:
        for mounted_device, mount in mounts_by_device.items():
            if mounted_device == device_name or mounted_device.startswith(device_name):
                return mount
        return {}
