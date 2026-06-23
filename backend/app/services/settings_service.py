from pathlib import Path
import logging

from ..database import get_connection
from ..models import utc_now_iso


logger = logging.getLogger(__name__)

DEFAULT_KWH_PRICE = 0.95
DEFAULT_CURRENCY = "BRL"


class SettingsService:
    def __init__(self, database_path: Path, allowed_intervals: set[int], default_interval: int) -> None:
        self.database_path = database_path
        self.allowed_intervals = allowed_intervals
        self.default_interval = default_interval

    def get_collect_interval(self) -> int:
        with get_connection(self.database_path) as connection:
            row = connection.execute(
                "SELECT value FROM settings WHERE key = 'collect_interval_seconds'"
            ).fetchone()
        if row is None:
            return self.default_interval
        return int(row["value"])

    def update_collect_interval(self, interval_seconds: int) -> int:
        if interval_seconds not in self.allowed_intervals:
            allowed = ", ".join(str(value) for value in sorted(self.allowed_intervals))
            raise ValueError(f"collect_interval_seconds must be one of: {allowed}")

        with get_connection(self.database_path) as connection:
            connection.execute(
                """
                INSERT INTO settings (key, value, updated_at)
                VALUES ('collect_interval_seconds', ?, ?)
                ON CONFLICT(key) DO UPDATE SET value = excluded.value, updated_at = excluded.updated_at
                """,
                (str(interval_seconds), utc_now_iso()),
            )
            connection.commit()

        logger.info("Collect interval changed to %s seconds", interval_seconds)
        return interval_seconds

    def get_energy_settings(self) -> dict:
        with get_connection(self.database_path) as connection:
            rows = connection.execute(
                "SELECT key, value FROM app_settings WHERE key IN ('energy.kwh_price', 'energy.currency')"
            ).fetchall()

        values = {row["key"]: row["value"] for row in rows}
        return {
            "kwhPrice": float(values.get("energy.kwh_price", DEFAULT_KWH_PRICE)),
            "currency": values.get("energy.currency", DEFAULT_CURRENCY),
        }

    def update_energy_settings(self, kwh_price: float, currency: str = DEFAULT_CURRENCY) -> dict:
        if kwh_price <= 0:
            raise ValueError("kwhPrice must be greater than zero")

        normalized_currency = currency.strip().upper() or DEFAULT_CURRENCY
        if len(normalized_currency) != 3:
            raise ValueError("currency must be a 3-letter code")

        with get_connection(self.database_path) as connection:
            timestamp = utc_now_iso()
            connection.executemany(
                """
                INSERT INTO app_settings (key, value, updated_at)
                VALUES (?, ?, ?)
                ON CONFLICT(key) DO UPDATE SET value = excluded.value, updated_at = excluded.updated_at
                """,
                (
                    ("energy.kwh_price", str(kwh_price), timestamp),
                    ("energy.currency", normalized_currency, timestamp),
                ),
            )
            connection.commit()

        logger.info("Energy settings changed to %s %s/kWh", normalized_currency, kwh_price)
        return {"kwhPrice": kwh_price, "currency": normalized_currency}
