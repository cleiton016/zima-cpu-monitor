from pydantic import BaseModel, Field


class SettingsPayload(BaseModel):
    collect_interval_seconds: int = Field(..., description="Allowed values: 5, 10, 30, 60, 300, 900")


class SettingsResponse(BaseModel):
    collect_interval_seconds: int


class HealthResponse(BaseModel):
    status: str


class EnergySettingsPayload(BaseModel):
    kwhPrice: float = Field(..., gt=0)
    currency: str = Field("BRL", min_length=3, max_length=3)


class EnergySettingsResponse(BaseModel):
    kwhPrice: float
    currency: str
