from fastapi import APIRouter, Query, Request


router = APIRouter(prefix="/api/metrics/storage", tags=["storage"])


@router.get("/current")
def storage_current(request: Request):
    return request.app.state.metrics_reader.read_storage_current()


@router.get("")
def storage_history(
    request: Request,
    device: str | None = Query(None),
    from_value: str | None = Query(None, alias="from"),
    to_value: str | None = Query(None, alias="to"),
    bucket: str | None = Query(None),
):
    return request.app.state.metrics_service.get_storage_history(device, from_value, to_value)
