from dataclasses import dataclass, field
from datetime import datetime, timezone


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


@dataclass
class CpuFrequency:
    current: float | None = None
    min: float | None = None
    max: float | None = None


@dataclass
class LoadAverage:
    one: float | None = None
    five: float | None = None
    fifteen: float | None = None


@dataclass
class TemperatureMetric:
    current: float | None = None
    max: float | None = None
    available: bool = False
    sensors: list[dict] = field(default_factory=list)


@dataclass
class PowerMetric:
    watts: float | None = None
    energy_joules: float | None = None
    available: bool = False


@dataclass
class MetricSnapshot:
    timestamp: str
    cpu_percent: float | None
    cpu_per_core: list[float]
    cpu_freq: CpuFrequency
    load: LoadAverage
    temperature: TemperatureMetric
    power: PowerMetric
    uptime_seconds: int | None

    def to_api_dict(self) -> dict:
        return {
            "timestamp": self.timestamp,
            "cpu_percent": self.cpu_percent,
            "cpu_per_core": self.cpu_per_core,
            "cpu_freq": {
                "current": self.cpu_freq.current,
                "min": self.cpu_freq.min,
                "max": self.cpu_freq.max,
            },
            "load": {
                "1": self.load.one,
                "5": self.load.five,
                "15": self.load.fifteen,
            },
            "temperature": {
                "current": self.temperature.current,
                "max": self.temperature.max,
                "available": self.temperature.available,
                "sensors": self.temperature.sensors,
            },
            "power": {
                "watts": self.power.watts,
                "energy_joules": self.power.energy_joules,
                "available": self.power.available,
            },
            "uptime_seconds": self.uptime_seconds,
        }
