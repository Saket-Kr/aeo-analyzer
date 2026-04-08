from fastapi import APIRouter

from app.models.schemas import FanOutRequest, FanOutResponse
from app.services.fanout_engine import run_fanout

router = APIRouter()


@router.post("/generate", response_model=FanOutResponse)
async def generate(request: FanOutRequest):
    return await run_fanout(request=request)
