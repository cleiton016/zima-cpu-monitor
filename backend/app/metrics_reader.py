from __future__ import annotations

from pathlib import Path
from time import monotonic
import logging
import os

try:
    import psutil
except ModuleNotFoundError:
    psutil = None

from .models import (
    CpuFrequency,
    LoadAverage,
    MetricSnapshot,
    PowerMetric,
    TemperatureMetric,
    utc_now_iso,
)


logger = logging.getLogger(__name__)


def normalize_temperature(raw_value: float) -> float:
    value = float(raw_value)
    if abs(value) > 1000:
        value = value / 1000
    return round(value, 2)


class MetricsReader:
    def __init__(self, host_sys_path: Path = Path("/sys"), host_proc_path: Path = Path("/proc")) -> None:
        self.host_sys_path = host_sys_path
        self.host_proc_path = host_proc_path
        self._last_energy_joules: float | None = None
        self._last_energy_time: float | None = None

    def read_all(self) -> MetricSnapshot:
        return MetricSnapshot(
            timestamp=utc_now_iso(),
            cpu_percent=self._safe_call(lambda: psutil.cpu_percent(interval=None) if psutil else None),
            cpu_per_core=self._safe_call(
                lambda: psutil.cpu_percent(interval=None, percpu=True) if psutil else [],
                default=[],
            ),
            cpu_freq=self._read_cpu_frequency(),
            load=self._read_load_average(),
            temperature=self.read_temperatures(),
            power=self.read_power(),
            uptime_seconds=self._read_uptime_seconds(),
        )

    def _read_cpu_frequency(self) -> CpuFrequency:
        if psutil is None:
            return CpuFrequency()
        freq = self._safe_call(psutil.cpu_freq)
        if not freq:
            return CpuFrequency()
        return CpuFrequency(
            current=round(freq.current, 2) if freq.current is not None else None,
            min=round(freq.min, 2) if freq.min is not None else None,
            max=round(freq.max, 2) if freq.max is not None else None,
        )

    def _read_load_average(self) -> LoadAverage:
        try:
            if psutil is not None:
                one, five, fifteen = psutil.getloadavg()
                return LoadAverage(round(one, 2), round(five, 2), round(fifteen, 2))
        except (AttributeError, OSError):
            pass

        try:
            one, five, fifteen = os.getloadavg()
            return LoadAverage(round(one, 2), round(five, 2), round(fifteen, 2))
        except (AttributeError, OSError):
            return LoadAverage()

    def read_temperatures(self) -> TemperatureMetric:
        sensors = self._read_psutil_temperatures()
        if not sensors:
            sensors = self._read_sys_temperatures()

        values = [sensor["value"] for sensor in sensors if sensor.get("value") is not None]
        if not values:
            return TemperatureMetric(available=False, sensors=[])

        return TemperatureMetric(
            current=round(max(values), 2),
            max=round(max(values), 2),
            available=True,
            sensors=sensors,
        )

    def read_power(self) -> PowerMetric:
        energy_joules = self._read_rapl_energy_joules()
        if energy_joules is None:
            return PowerMetric(available=False)

        now = monotonic()
        watts = None
        # RAPL exposes accumulated energy. Watts can only be estimated after two readings.
        if self._last_energy_joules is not None and self._last_energy_time is not None:
            delta_energy = energy_joules - self._last_energy_joules
            delta_time = now - self._last_energy_time
            if delta_energy >= 0 and delta_time > 0:
                watts = round(delta_energy / delta_time, 2)

        self._last_energy_joules = energy_joules
        self._last_energy_time = now
        return PowerMetric(watts=watts, energy_joules=round(energy_joules, 2), available=True)

    def _read_psutil_temperatures(self) -> list[dict]:
        if psutil is None:
            return []
        try:
            raw_sensors = psutil.sensors_temperatures(fahrenheit=False)
        except (AttributeError, OSError) as exc:
            logger.debug("psutil temperature sensors unavailable: %s", exc)
            return []

        sensors: list[dict] = []
        for chip_name, entries in raw_sensors.items():
            for entry in entries:
                if entry.current is None:
                    continue
                sensors.append(
                    {
                        "source": "psutil",
                        "chip": chip_name,
                        "label": entry.label or chip_name,
                        "value": normalize_temperature(entry.current),
                    }
                )
        return sensors

    def _read_sys_temperatures(self) -> list[dict]:
        sensors: list[dict] = []
        patterns = [
            "class/thermal/thermal_zone*/temp",
            "class/hwmon/hwmon*/temp*_input",
        ]

        for pattern in patterns:
            for path in self.host_sys_path.glob(pattern):
                value = self._read_temperature_file(path)
                if value is None:
                    continue
                sensors.append(
                    {
                        "source": "sysfs",
                        "chip": path.parent.name,
                        "label": self._read_sensor_label(path),
                        "value": value,
                    }
                )
        return sensors

    def _read_sensor_label(self, temp_path: Path) -> str:
        label_path = temp_path.with_name(temp_path.name.replace("_input", "_label"))
        if label_path.exists():
            try:
                return label_path.read_text(encoding="utf-8").strip()
            except OSError:
                pass
        return temp_path.name

    def _read_temperature_file(self, path: Path) -> float | None:
        try:
            return normalize_temperature(float(path.read_text(encoding="utf-8").strip()))
        except (OSError, ValueError):
            logger.debug("Failed to read temperature file %s", path)
            return None

    def _read_rapl_energy_joules(self) -> float | None:
        powercap_path = self.host_sys_path / "class" / "powercap"
        total_energy_uj = 0
        found = False

        energy_paths = {
            *powercap_path.glob("intel-rapl:*/energy_uj"),
            *powercap_path.glob("intel-rapl*/energy_uj"),
        }

        for energy_path in energy_paths:
            try:
                total_energy_uj += int(energy_path.read_text(encoding="utf-8").strip())
                found = True
            except (OSError, ValueError):
                logger.debug("Failed to read RAPL energy file %s", energy_path)

        if not found:
            return None
        return total_energy_uj / 1_000_000

    def _read_uptime_seconds(self) -> int | None:
        if psutil is None:
            return None
        uptime = self._safe_call(psutil.boot_time)
        if uptime is None:
            return None
        return max(0, int(__import__("time").time() - uptime))

    def _safe_call(self, callback, default=None):
        try:
            result = callback()
            return default if result is None else result
        except Exception as exc:
            logger.debug("Metric read failed: %s", exc)
            return default
