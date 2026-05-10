"""分镜生成端点。"""

from fastapi import APIRouter, Query

from app.schemas.scene import Scene
from app.services import outline_service

router = APIRouter()


@router.get(
    "",
    response_model=list[Scene],
    summary="按主题生成分镜列表（优先 LLM，失败回退模板）",
)
async def generate_scenes(
    topic: str = Query(..., min_length=1, description="主题文本"),
) -> list[Scene]:
    return await outline_service.generate_scenes(topic)
