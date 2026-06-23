from pathlib import Path

import pytest

from app.database import initialize_database
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
