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

    def read_ram_current(self) -> dict:
        timestamp = utc_now_iso()
        meminfo = self._parse_meminfo()
        virtual = psutil.virtual_memory() if psutil else None
        swap = psutil.swap_memory() if psutil else None

        total = virtual.total if virtual else meminfo.get("MemTotal", 0)
        available = virtual.available if virtual else meminfo.get("MemAvailable", 0)
        free = virtual.free if virtual else meminfo.get("MemFree")
        used = virtual.used if virtual else max(0, total - available)
        swap_total = swap.total if swap else meminfo.get("SwapTotal")
        swap_used = swap.used if swap else self._swap_used_from_meminfo(meminfo)

        return {
            "timestamp": timestamp,
            "totalBytes": total,
            "usedBytes": used,
            "availableBytes": available,
            "freeBytes": free,
            "usagePercent": round((used / total) * 100, 2) if total else 0,
            "buffersBytes": meminfo.get("Buffers"),
            "cachedBytes": meminfo.get("Cached"),
            "sharedBytes": meminfo.get("Shmem"),
            "swapTotalBytes": swap_total,
            "swapUsedBytes": swap_used,
            "swapUsagePercent": round((swap_used / swap_total) * 100, 2) if swap_total else 0,
            "temperatureCelsius": None,
        }

    def read_ram_processes(self, limit: int = 10) -> dict:
        timestamp = utc_now_iso()
        if psutil is None:
            return {"timestamp": timestamp, "processes": []}

        processes = []
        for process in psutil.process_iter(["pid", "name", "cmdline", "memory_info", "memory_percent"]):
            try:
                info = process.info
                memory_info = info.get("memory_info")
                command = " ".join(info.get("cmdline") or [])
                processes.append(
                    {
                        "pid": info.get("pid"),
                        "name": info.get("name"),
                        "command": command or info.get("name"),
                        "memoryBytes": memory_info.rss if memory_info else None,
                        "memoryPercent": round(info.get("memory_percent") or 0, 2),
                    }
                )
            except (psutil.NoSuchProcess, psutil.AccessDenied, OSError):
                continue

        processes.sort(key=lambda item: item["memoryBytes"] or 0, reverse=True)
        return {"timestamp": timestamp, "processes": processes[:limit]}

    def read_storage_current(self) -> dict:
        timestamp = utc_now_iso()
        devices = self._read_storage_devices()
        mounts = self._read_storage_mounts()
        return {"timestamp": timestamp, "devices": devices, "mounts": mounts}

    def read_gpu_current(self) -> dict:
        timestamp = utc_now_iso()
        devices = []
        drm_path = self.host_sys_path / "class" / "drm"
        for card_path in sorted(drm_path.glob("card[0-9]*")):
            if "-" in card_path.name:
                continue
            devices.append(
                {
                    "id": card_path.name,
                    "vendor": self._read_gpu_vendor(card_path),
                    "model": self._read_text(card_path / "device" / "uevent") or card_path.name,
                    "driver": self._read_driver_name(card_path),
                    "usagePercent": self._read_text(card_path / "device" / "hwmon" / "pwm1") or None,
                    "temperatureCelsius": self._read_text(card_path / "device" / "hwmon" / "temp1_input"),
                    "memoryTotalBytes": self._read_text(card_path / "device" / "hwmon" / "mem_total_bytes"),
                    "memoryUsedBytes": self._read_text(card_path / "device" / "hwmon" / "mem_used_bytes"),
                    "memoryUsagePercent": self._read_text(card_path / "device" / "hwmon" / "mem_usage_percent"),
                    "powerWatts": self._read_text(card_path / "device" / "hwmon" / "power1_input"),
                }
            )
        return {"available": bool(devices), "timestamp": timestamp, "devices": devices}

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

    def _read_storage_devices(self) -> list[dict]:
        disk_io = psutil.disk_io_counters(perdisk=True) if psutil else {}
        devices: list[dict] = []
        for device_path in sorted((self.host_sys_path / "block").glob("*")):
            name = device_path.name
            model = self._read_text(device_path / "device" / "model")
            if not self._is_storage_disk_name(name):
                continue
            if not model:
                continue
            size_bytes = self._read_block_size(device_path)
            # size deve ser maior que 500mb
            if size_bytes is None or size_bytes < 500 * 1024 * 1024:
                continue
            io = disk_io.get(name) if disk_io else None
            devices.append(
                {
                    "name": name,
                    "model": model,
                    "type": self._read_disk_type(device_path),
                    "sizeBytes": size_bytes,
                    "temperatureCelsius": None,
                    "smartStatus": None,
                    "readBytesTotal": io.read_bytes if io else None,
                    "writeBytesTotal": io.write_bytes if io else None,
                    "readBytesPerSecond": None,
                    "writeBytesPerSecond": None,
                }
            )
        return devices

    def _read_storage_mounts(self) -> list[dict]:
        if psutil is None:
            return []
        mounts = []
        for partition in psutil.disk_partitions(all=False):
            try:
                usage = psutil.disk_usage(partition.mountpoint)
            except OSError:
                continue
            mounts.append(
                {
                    "device": partition.device,
                    "mountPoint": partition.mountpoint,
                    "filesystem": partition.fstype,
                    "totalBytes": usage.total,
                    "usedBytes": usage.used,
                    "freeBytes": usage.free,
                    "usagePercent": usage.percent,
                }
            )
        return mounts

    def _is_storage_disk_name(self, name: str) -> bool:
        if name.startswith(("loop", "ram", "dm-", "zram", "sr", "fd")):
            return False
        return True

    def _parse_meminfo(self) -> dict[str, int]:
        meminfo_path = self.host_proc_path / "meminfo"
        values: dict[str, int] = {}
        try:
            lines = meminfo_path.read_text(encoding="utf-8", errors="ignore").splitlines()
        except OSError:
            return values
        for line in lines:
            if ":" not in line:
                continue
            key, raw_value = line.split(":", 1)
            parts = raw_value.strip().split()
            if not parts:
                continue
            try:
                values[key] = int(parts[0]) * 1024
            except ValueError:
                continue
        return values

    def _swap_used_from_meminfo(self, meminfo: dict[str, int]) -> int | None:
        total = meminfo.get("SwapTotal")
        free = meminfo.get("SwapFree")
        if total is None or free is None:
            return None
        return max(0, total - free)

    def _read_block_size(self, device_path: Path) -> int | None:
        try:
            sectors = int((device_path / "size").read_text(encoding="utf-8").strip())
        except (OSError, ValueError):
            return None
        return sectors * 512

    def _read_disk_type(self, device_path: Path) -> str:
        if device_path.name.startswith("nvme"):
            return "NVMe"
        rotational = self._read_text(device_path / "queue" / "rotational")
        if rotational == "0":
            return "SSD"
        if rotational == "1":
            return "HDD"
        return "unknown"

    def _read_gpu_vendor(self, card_path: Path) -> str | None:
        vendor_id = self._read_text(card_path / "device" / "vendor")
        vendor_map = {
            "0x8086": "Intel",
            "0x10de": "NVIDIA",
            "0x1002": "AMD",
            "0x1022": "AMD",
        }
        return vendor_map.get((vendor_id or "").lower())

    def _read_driver_name(self, card_path: Path) -> str | None:
        try:
            return (card_path / "device" / "driver").resolve().name
        except OSError:
            return None

    def _read_text(self, path: Path) -> str | None:
        try:
            value = path.read_text(encoding="utf-8", errors="ignore").strip()
        except OSError:
            return None
        return value or None

    def _safe_call(self, callback, default=None):
        try:
            result = callback()
            return default if result is None else result
        except Exception as exc:
            logger.debug("Metric read failed: %s", exc)
            return default
