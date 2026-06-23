from __future__ import annotations

from pathlib import Path
import logging
import platform
import shutil
import subprocess

try:
    import psutil
except ModuleNotFoundError:
    psutil = None


logger = logging.getLogger(__name__)


class HardwareInfoReader:
    def __init__(self, host_sys_path: Path = Path("/sys"), host_proc_path: Path = Path("/proc")) -> None:
        self.host_sys_path = host_sys_path
        self.host_proc_path = host_proc_path

    def read(self) -> dict:
        return {
            "cpu": self._read_cpu(),
            "motherboard": self._read_motherboard(),
            "gpu": self._read_gpu(),
            "storage": self._read_storage(),
            "memory": self._read_memory(),
        }

    def _read_cpu(self) -> dict:
        cpuinfo = self._parse_cpuinfo()
        lscpu = self._parse_key_value_command(["lscpu"])
        physical_cores = self._read_physical_cores()
        threads = psutil.cpu_count(logical=True) if psutil else None
        freq = psutil.cpu_freq() if psutil else None

        return {
            "model": cpuinfo.get("model name") or lscpu.get("Model name"),
            "vendor": cpuinfo.get("vendor_id") or lscpu.get("Vendor ID"),
            "architecture": lscpu.get("Architecture") or platform.machine() or None,
            "physicalCores": physical_cores,
            "threads": threads,
            "baseFrequencyMHz": self._float_or_none(lscpu.get("CPU min MHz")),
            "currentFrequencyMHz": round(freq.current, 2) if freq and freq.current is not None else None,
            "cache": cpuinfo.get("cache size") or lscpu.get("L3 cache") or lscpu.get("L2 cache"),
        }

    def _read_motherboard(self) -> dict:
        dmi_path = self.host_sys_path / "class" / "dmi" / "id"
        return {
            "vendor": self._read_text(dmi_path / "board_vendor"),
            "model": self._read_text(dmi_path / "board_name"),
            "version": self._read_text(dmi_path / "board_version"),
            "serial": self._read_text(dmi_path / "board_serial"),
            "biosVendor": self._read_text(dmi_path / "bios_vendor"),
            "biosVersion": self._read_text(dmi_path / "bios_version"),
            "biosDate": self._read_text(dmi_path / "bios_date"),
        }

    def _read_gpu(self) -> dict:
        pci_lines = self._run_command(["lspci"])
        gpu_line = next(
            (
                line
                for line in pci_lines
                if any(marker in line.lower() for marker in ("vga compatible controller", "3d controller", "display controller"))
            ),
            None,
        )

        drm_devices = [path.name for path in (self.host_sys_path / "class" / "drm").glob("card[0-9]*")]
        available = bool(gpu_line or drm_devices)
        vendor, model = self._split_gpu_line(gpu_line)

        return {
            "available": available,
            "vendor": vendor,
            "model": model or (drm_devices[0] if drm_devices else None),
            "driver": self._read_gpu_driver(drm_devices[0]) if drm_devices else None,
            "memoryTotalBytes": None,
            "temperatureCelsius": None,
            "usagePercent": None,
        }

    def _read_storage(self) -> list[dict]:
        disks: list[dict] = []
        for device_path in sorted((self.host_sys_path / "block").glob("*")):
            name = device_path.name
            if name.startswith(("loop", "ram", "dm-")):
                continue
            size_bytes = self._read_block_size(device_path)
            mount = self._find_mount_for_device(name)
            disks.append(
                {
                    "name": name,
                    "model": self._read_text(device_path / "device" / "model"),
                    "serial": self._read_text(device_path / "device" / "serial"),
                    "type": self._read_disk_type(device_path),
                    "sizeBytes": size_bytes,
                    "usedBytes": mount["usedBytes"] if mount else None,
                    "freeBytes": mount["freeBytes"] if mount else None,
                    "usagePercent": mount["usagePercent"] if mount else None,
                    "temperatureCelsius": None,
                    "smartStatus": None,
                }
            )
        return disks

    def _read_memory(self) -> dict:
        virtual = psutil.virtual_memory() if psutil else None
        swap = psutil.swap_memory() if psutil else None
        if virtual:
            used = virtual.total - virtual.available
            total = virtual.total
            available = virtual.available
            free = virtual.free
        else:
            meminfo = self._parse_meminfo()
            total = meminfo.get("MemTotal")
            available = meminfo.get("MemAvailable")
            free = meminfo.get("MemFree")
            used = total - available if total is not None and available is not None else None

        return {
            "totalBytes": total,
            "usedBytes": used,
            "availableBytes": available,
            "freeBytes": free,
            "swapTotalBytes": swap.total if swap else self._parse_meminfo().get("SwapTotal"),
            "swapUsedBytes": swap.used if swap else self._swap_used_from_meminfo(),
            "temperatureCelsius": None,
        }

    def _parse_cpuinfo(self) -> dict[str, str]:
        cpuinfo_path = self.host_proc_path / "cpuinfo"
        try:
            content = cpuinfo_path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            return {}

        values: dict[str, str] = {}
        for line in content.splitlines():
            if ":" not in line:
                continue
            key, value = line.split(":", 1)
            values.setdefault(key.strip(), value.strip())
        return values

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
            if parts:
                values[key] = int(parts[0]) * 1024
        return values

    def _read_physical_cores(self) -> int | None:
        if psutil:
            cores = psutil.cpu_count(logical=False)
            if cores is not None:
                return cores
        cpu_dirs = list((self.host_sys_path / "devices" / "system" / "cpu").glob("cpu[0-9]*"))
        return len(cpu_dirs) or None

    def _find_mount_for_device(self, name: str) -> dict | None:
        if not psutil:
            return None
        candidates = [partition for partition in psutil.disk_partitions(all=False) if Path(partition.device).name.startswith(name)]
        if not candidates:
            return None
        try:
            usage = psutil.disk_usage(candidates[0].mountpoint)
        except OSError:
            return None
        return {
            "usedBytes": usage.used,
            "freeBytes": usage.free,
            "usagePercent": usage.percent,
        }

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

    def _read_gpu_driver(self, card_name: str) -> str | None:
        driver_link = self.host_sys_path / "class" / "drm" / card_name / "device" / "driver"
        try:
            return driver_link.resolve().name
        except OSError:
            return None

    def _split_gpu_line(self, line: str | None) -> tuple[str | None, str | None]:
        if not line:
            return None, None
        model = line.split(":", 2)[-1].strip()
        lowered = model.lower()
        for vendor in ("Intel", "NVIDIA", "AMD", "ATI"):
            if vendor.lower() in lowered:
                return vendor, model
        return None, model

    def _parse_key_value_command(self, command: list[str]) -> dict[str, str]:
        values: dict[str, str] = {}
        for line in self._run_command(command):
            if ":" not in line:
                continue
            key, value = line.split(":", 1)
            values[key.strip()] = value.strip()
        return values

    def _run_command(self, command: list[str]) -> list[str]:
        if shutil.which(command[0]) is None:
            return []
        try:
            result = subprocess.run(command, capture_output=True, check=False, text=True, timeout=2)
        except (OSError, subprocess.SubprocessError) as exc:
            logger.debug("Hardware command failed: %s", exc)
            return []
        if result.returncode != 0:
            return []
        return result.stdout.splitlines()

    def _swap_used_from_meminfo(self) -> int | None:
        meminfo = self._parse_meminfo()
        total = meminfo.get("SwapTotal")
        free = meminfo.get("SwapFree")
        if total is None or free is None:
            return None
        return max(0, total - free)

    def _read_text(self, path: Path) -> str | None:
        try:
            value = path.read_text(encoding="utf-8", errors="ignore").strip()
        except OSError:
            return None
        return value or None

    def _float_or_none(self, value: str | None) -> float | None:
        if value is None:
            return None
        try:
            return float(value)
        except ValueError:
            return None
