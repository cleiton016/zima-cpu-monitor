from fastapi import APIRouter, Query, Request


router = APIRouter(prefix="/api/metrics/gpu", tags=["gpu"])


@router.get("/current")
def gpu_current(request: Request):
    return request.app.state.metrics_reader.read_gpu_current()


@router.get("")
def gpu_history(
    request: Request,
    from_value: str | None = Query(None, alias="from"),
    to_value: str | None = Query(None, alias="to"),
    bucket: str | None = Query(None),
):
    return request.app.state.metrics_service.get_gpu_history(from_value, to_value)
