from fastapi import APIRouter, HTTPException, Query, Request


router = APIRouter(prefix="/api/metrics", tags=["metrics"])


@router.get("/current")
def current_metric(request: Request):
    collector = request.app.state.collector
    if collector.current_metric:
        return collector.current_metric

    latest = request.app.state.metrics_service.get_latest()
    if latest:
        return latest

    metric = request.app.state.metrics_reader.read_all()
    return metric.to_api_dict()


@router.get("/history")
def metric_history(
    request: Request,
    range_name: str | None = Query("24h", alias="range"),
    from_value: str | None = Query(None, alias="from"),
    to_value: str | None = Query(None, alias="to"),
):
    try:
        return request.app.state.metrics_service.get_history(range_name, from_value, to_value)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/summary")
def metric_summary(
    request: Request,
    range_name: str | None = Query("24h", alias="range"),
    from_value: str | None = Query(None, alias="from"),
    to_value: str | None = Query(None, alias="to"),
):
    try:
        return request.app.state.metrics_service.get_summary(range_name, from_value, to_value)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
