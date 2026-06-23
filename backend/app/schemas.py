from pydantic import BaseModel, Field


class SettingsPayload(BaseModel):
    collect_interval_seconds: int = Field(..., description="Allowed values: 5, 10, 30, 60, 300, 900")


class SettingsResponse(BaseModel):
    collect_interval_seconds: int


class HealthResponse(BaseModel):
    status: str
