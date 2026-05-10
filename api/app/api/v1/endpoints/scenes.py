"""分镜生成端点。"""

from fastapi import APIRouter, Query

from app.schemas.scene import Scene
from app.services import outline_service

router = APIRouter()


@router.get(
    "",
    response_model=list[Scene],
    summary="按主题一次性生成分镜列表",
)
async def generate_scenes(
    topic: str = Query(..., min_length=1, description="主题文本"),
) -> list[Scene]:
    return outline_service.generate_scenes_sync(topic)
