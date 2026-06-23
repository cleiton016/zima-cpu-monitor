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
                self.current_metric = metric.to_api_dict()
            except Exception:
                logger.exception("Failed to collect metrics")
            await asyncio.sleep(interval)
