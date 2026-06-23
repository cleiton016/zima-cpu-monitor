from pathlib import Path

from app.metrics_reader import MetricsReader, normalize_temperature


def test_normalize_temperature_converts_millicelsius():
    assert normalize_temperature(55000) == 55.0
    assert normalize_temperature(42.4) == 42.4


def test_reads_sysfs_temperature_fallback(tmp_path: Path):
    sensor_dir = tmp_path / "class" / "thermal" / "thermal_zone0"
    sensor_dir.mkdir(parents=True)
    (sensor_dir / "temp").write_text("53000", encoding="utf-8")

    metric = MetricsReader(host_sys_path=tmp_path).read_temperatures()

    assert metric.available is True
    assert metric.current == 53.0
    assert metric.sensors[0]["source"] == "sysfs"


def test_calculates_rapl_watts(tmp_path: Path, monkeypatch):
    rapl_dir = tmp_path / "class" / "powercap" / "intel-rapl0"
    rapl_dir.mkdir(parents=True)
    energy_file = rapl_dir / "energy_uj"
    energy_file.write_text("1000000", encoding="utf-8")
    reader = MetricsReader(host_sys_path=tmp_path)

    times = iter([10.0, 12.0])
    monkeypatch.setattr("app.metrics_reader.monotonic", lambda: next(times))

    first = reader.read_power()
    energy_file.write_text("3000000", encoding="utf-8")
    second = reader.read_power()

    assert first.available is True
    assert first.watts is None
    assert second.energy_joules == 3.0
    assert second.watts == 1.0
