from fastapi import APIRouter, Query, Request


router = APIRouter(prefix="/api/metrics/ram", tags=["ram"])


@router.get("/current")
def ram_current(request: Request):
    return request.app.state.metrics_reader.read_ram_current()


@router.get("")
def ram_history(
    request: Request,
    from_value: str | None = Query(None, alias="from"),
    to_value: str | None = Query(None, alias="to"),
    bucket: str | None = Query(None),
):
    return request.app.state.metrics_service.get_ram_history(from_value, to_value)


@router.get("/processes")
def ram_processes(request: Request):
    return request.app.state.metrics_reader.read_ram_processes()


@router.delete("/history")
def clear_ram_history(request: Request):
    return request.app.state.metrics_service.clear_history("ram")
