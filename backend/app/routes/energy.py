from fastapi import APIRouter, Query, Request


router = APIRouter(prefix="/api/metrics/energy", tags=["energy"])


@router.get("")
def energy_history(
    request: Request,
    from_value: str | None = Query(None, alias="from"),
    to_value: str | None = Query(None, alias="to"),
    bucket: str | None = Query(None),
):
    return request.app.state.metrics_service.get_energy_history(from_value, to_value)


@router.get("/monthly")
def energy_monthly(request: Request, year: int | None = Query(None)):
    return request.app.state.metrics_service.get_energy_monthly(year)


@router.delete("/history")
def clear_energy_history(request: Request):
    return request.app.state.metrics_service.clear_history("energy")
