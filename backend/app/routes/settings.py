from fastapi import APIRouter, HTTPException, Request

from ..schemas import SettingsPayload, SettingsResponse


router = APIRouter(prefix="/api/settings", tags=["settings"])


@router.get("", response_model=SettingsResponse)
def get_settings(request: Request):
    interval = request.app.state.settings_service.get_collect_interval()
    return SettingsResponse(collect_interval_seconds=interval)


@router.put("", response_model=SettingsResponse)
def update_settings(request: Request, payload: SettingsPayload):
    try:
        interval = request.app.state.settings_service.update_collect_interval(payload.collect_interval_seconds)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return SettingsResponse(collect_interval_seconds=interval)
