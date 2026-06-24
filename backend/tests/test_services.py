from pathlib import Path

import pytest

from app.database import initialize_database
from app.database import get_connection
from app.models import CpuFrequency, LoadAverage, MetricSnapshot, PowerMetric, TemperatureMetric
from app.services.metrics_service import MetricsService
from app.services.settings_service import SettingsService


def make_metric(timestamp: str = "2026-06-23T10:00:00Z") -> MetricSnapshot:
    return MetricSnapshot(
        timestamp=timestamp,
        cpu_percent=25.5,
        cpu_per_core=[20.0, 31.0],
        cpu_freq=CpuFrequency(current=1800.0, min=800.0, max=3200.0),
        load=LoadAverage(one=0.5, five=0.4, fifteen=0.3),
        temperature=TemperatureMetric(current=55.0, max=55.0, available=True, sensors=[]),
        power=PowerMetric(watts=8.0, energy_joules=100.0, available=True),
        uptime_seconds=120,
    )


def test_metric_insert_and_history(tmp_path: Path):
    database_path = tmp_path / "metrics.db"
    initialize_database(database_path, 30)
    service = MetricsService(database_path)

    service.save(make_metric())
    history = service.get_history(from_value="2026-06-23T00:00:00Z", to_value="2026-06-24T00:00:00Z")

    assert len(history) == 1
    assert history[0]["cpu_percent"] == 25.5
    assert history[0]["temperature"]["available"] is True
    assert history[0]["power"]["available"] is True


def test_settings_service_accepts_allowed_interval(tmp_path: Path):
    database_path = tmp_path / "metrics.db"
    initialize_database(database_path, 30)
    service = SettingsService(database_path, {5, 10, 30}, 30)

    assert service.get_collect_interval() == 30
    assert service.update_collect_interval(10) == 10
    assert service.get_collect_interval() == 10


def test_settings_service_rejects_invalid_interval(tmp_path: Path):
    database_path = tmp_path / "metrics.db"
    initialize_database(database_path, 30)
    service = SettingsService(database_path, {5, 10, 30}, 30)

    with pytest.raises(ValueError):
        service.update_collect_interval(99)


def test_initialize_database_creates_extended_tables(tmp_path: Path):
    database_path = tmp_path / "metrics.db"
    initialize_database(database_path, 30)

    with get_connection(database_path) as connection:
        rows = connection.execute(
            """
            SELECT name FROM sqlite_master
            WHERE type = 'table'
            AND name IN (
                'app_settings',
                'ram_samples',
                'process_memory_samples',
                'storage_samples',
                'storage_mount_samples',
                'gpu_samples',
                'energy_samples'
            )
            """
        ).fetchall()

    assert {row["name"] for row in rows} == {
        "app_settings",
        "ram_samples",
        "process_memory_samples",
        "storage_samples",
        "storage_mount_samples",
        "gpu_samples",
        "energy_samples",
    }


def test_energy_settings_are_persisted(tmp_path: Path):
    database_path = tmp_path / "metrics.db"
    initialize_database(database_path, 30)
    service = SettingsService(database_path, {5, 10, 30}, 30)

    assert service.get_energy_settings() == {"kwhPrice": 0.95, "currency": "BRL"}
    assert service.update_energy_settings(1.05, "brl") == {"kwhPrice": 1.05, "currency": "BRL"}
    assert service.get_energy_settings() == {"kwhPrice": 1.05, "currency": "BRL"}


def test_daily_summary_uses_metrics_and_energy_samples(tmp_path: Path):
    database_path = tmp_path / "metrics.db"
    initialize_database(database_path, 30)
    service = MetricsService(database_path)
    service.save(make_metric("2026-06-23T10:00:00Z"))
    service.save_energy_sample("2026-06-23T10:00:00Z", 10.0, 0.5, "test")

    with get_connection(database_path) as connection:
        connection.execute(
            """
            INSERT INTO ram_samples (
                timestamp, total_bytes, used_bytes, available_bytes, usage_percent, created_at
            ) VALUES ('2026-06-23T10:00:00Z', 100, 80, 20, 80.0, '2026-06-23T10:00:00Z')
            """
        )
        connection.commit()

    summary = service.get_daily_summary("2026-06-23")

    assert summary["cpuPeak"]["valuePercent"] == 25.5
    assert summary["temperaturePeak"]["valueCelsius"] == 55.0
    assert summary["ramPeak"]["valuePercent"] == 80.0
    assert summary["energyTotal"]["kwh"] == 0.5
    assert summary["energyTotal"]["estimatedCost"] == 0.47


def test_clear_history_deletes_only_requested_category(tmp_path: Path):
    database_path = tmp_path / "metrics.db"
    initialize_database(database_path, 30)
    service = MetricsService(database_path)
    service.save(make_metric("2026-06-23T10:00:00Z"))

    with get_connection(database_path) as connection:
        connection.execute(
            """
            INSERT INTO ram_samples (
                timestamp, total_bytes, used_bytes, available_bytes, usage_percent, created_at
            ) VALUES ('2026-06-23T10:00:00Z', 100, 80, 20, 80.0, '2026-06-23T10:00:00Z')
            """
        )
        connection.execute(
            """
            INSERT INTO process_memory_samples (
                timestamp, pid, name, command, memory_bytes, memory_percent, created_at
            ) VALUES ('2026-06-23T10:00:00Z', 123, 'python', 'python app.py', 10, 1.0, '2026-06-23T10:00:00Z')
            """
        )
        connection.execute(
            """
            INSERT INTO storage_samples (
                timestamp, device_name, created_at
            ) VALUES ('2026-06-23T10:00:00Z', 'sda', '2026-06-23T10:00:00Z')
            """
        )
        connection.execute(
            """
            INSERT INTO storage_mount_samples (
                timestamp, mount_point, created_at
            ) VALUES ('2026-06-23T10:00:00Z', '/DATA', '2026-06-23T10:00:00Z')
            """
        )
        connection.execute(
            """
            INSERT INTO gpu_samples (
                timestamp, gpu_id, created_at
            ) VALUES ('2026-06-23T10:00:00Z', 'card0', '2026-06-23T10:00:00Z')
            """
        )
        connection.execute(
            """
            INSERT INTO energy_samples (
                timestamp, power_watts, energy_kwh, source, created_at
            ) VALUES ('2026-06-23T10:00:00Z', 10.0, 0.5, 'test', '2026-06-23T10:00:00Z')
            """
        )
        connection.commit()

    result = service.clear_history("ram")

    with get_connection(database_path) as connection:
        counts = {
            table: connection.execute(f"SELECT COUNT(*) AS count FROM {table}").fetchone()["count"]
            for table in (
                "metrics",
                "ram_samples",
                "process_memory_samples",
                "storage_samples",
                "storage_mount_samples",
                "gpu_samples",
                "energy_samples",
            )
        }

    assert result == {"category": "ram", "deletedRows": 2}
    assert counts == {
        "metrics": 1,
        "ram_samples": 0,
        "process_memory_samples": 0,
        "storage_samples": 1,
        "storage_mount_samples": 1,
        "gpu_samples": 1,
        "energy_samples": 1,
    }


def test_clear_history_rejects_unknown_category(tmp_path: Path):
    database_path = tmp_path / "metrics.db"
    initialize_database(database_path, 30)
    service = MetricsService(database_path)

    with pytest.raises(ValueError):
        service.clear_history("unknown")
