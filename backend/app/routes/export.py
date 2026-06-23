from fastapi import APIRouter, HTTPException, Query, Request
from fastapi.responses import Response


router = APIRouter(prefix="/api/export", tags=["export"])


@router.get("/csv")
def export_csv(
    request: Request,
    range_name: str | None = Query("24h", alias="range"),
    from_value: str | None = Query(None, alias="from"),
    to_value: str | None = Query(None, alias="to"),
):
    try:
        csv_body = request.app.state.metrics_service.export_csv(range_name, from_value, to_value)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return Response(
        content=csv_body,
        media_type="text/csv",
        headers={"Content-Disposition": 'attachment; filename="zima-cpu-monitor.csv"'},
    )
