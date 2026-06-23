from contextlib import asynccontextmanager
import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .collector import Collector
from .config import get_settings
from .database import initialize_database
from .metrics_reader import MetricsReader
from .routes import export, metrics, settings as settings_routes
from .schemas import HealthResponse
from .services.metrics_service import MetricsService
from .services.settings_service import SettingsService


logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    app_settings = get_settings()
    logger.info("Initializing Zima CPU Monitor backend")
    initialize_database(app_settings.database_path, app_settings.default_collect_interval_seconds)

    app.state.metrics_reader = MetricsReader(app_settings.host_sys_path, app_settings.host_proc_path)
    app.state.metrics_service = MetricsService(app_settings.database_path)
    app.state.settings_service = SettingsService(
        app_settings.database_path,
        app_settings.allowed_collect_intervals,
        app_settings.default_collect_interval_seconds,
    )
    app.state.collector = Collector(
        app.state.metrics_reader,
        app.state.metrics_service,
        app.state.settings_service,
    )
    app.state.collector.start()

    yield

    await app.state.collector.stop()


app = FastAPI(title="Zima CPU Monitor", version="0.1.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health", response_model=HealthResponse)
def health():
    return HealthResponse(status="ok")


app.include_router(metrics.router)
app.include_router(settings_routes.router)
app.include_router(export.router)
