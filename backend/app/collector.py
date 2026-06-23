import asyncio
import logging

from .metrics_reader import MetricsReader
from .services.metrics_service import MetricsService
from .services.settings_service import SettingsService


logger = logging.getLogger(__name__)


class Collector:
    def __init__(
        self,
        metrics_reader: MetricsReader,
        metrics_service: MetricsService,
        settings_service: SettingsService,
    ) -> None:
        self.metrics_reader = metrics_reader
        self.metrics_service = metrics_service
        self.settings_service = settings_service
        self.current_metric: dict | None = None
        self._task: asyncio.Task | None = None

    def start(self) -> None:
        if self._task is None:
            logger.info("Starting metrics collector")
            self._task = asyncio.create_task(self.loop())

    async def stop(self) -> None:
        if self._task is None:
            return
        self._task.cancel()
        try:
            await self._task
        except asyncio.CancelledError:
            logger.info("Metrics collector stopped")

    async def loop(self) -> None:
        while True:
            interval = 30
            try:
                interval = self.settings_service.get_collect_interval()
                logger.debug("Collect interval is %s seconds", interval)
                metric = self.metrics_reader.read_all()
                self.metrics_service.save(metric)
                self._collect_extended_metrics(metric.timestamp, metric.power.watts, interval)
                self.current_metric = metric.to_api_dict()
            except Exception:
                logger.exception("Failed to collect metrics")
            await asyncio.sleep(interval)

    def _collect_extended_metrics(self, timestamp: str, power_watts: float | None, interval: int) -> None:
        collectors = (
            self._collect_ram,
            self._collect_storage,
            self._collect_gpu,
            lambda: self._collect_energy(timestamp, power_watts, interval),
        )
        for collect in collectors:
            try:
                collect()
            except Exception:
                logger.exception("Extended metric collection failed")

    def _collect_ram(self) -> None:
        self.metrics_service.save_ram_sample(self.metrics_reader.read_ram_current())
        self.metrics_service.save_process_memory_samples(self.metrics_reader.read_ram_processes())

    def _collect_storage(self) -> None:
        self.metrics_service.save_storage_current(self.metrics_reader.read_storage_current())

    def _collect_gpu(self) -> None:
        self.metrics_service.save_gpu_current(self.metrics_reader.read_gpu_current())

    def _collect_energy(self, timestamp: str, power_watts: float | None, interval: int) -> None:
        energy_kwh = None
        if power_watts is not None:
            energy_kwh = (power_watts * (interval / 3600)) / 1000
        self.metrics_service.save_energy_sample(timestamp, power_watts, energy_kwh, "intel-rapl")
