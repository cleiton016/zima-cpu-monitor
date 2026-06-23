from fastapi import APIRouter, Request


router = APIRouter(prefix="/api/hardware", tags=["hardware"])


@router.get("/info")
def hardware_info(request: Request):
    return request.app.state.hardware_info_reader.read()
