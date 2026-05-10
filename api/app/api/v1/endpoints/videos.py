"""视频任务端点。"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.schemas.video import VideoCreateRequest, VideoDetail, VideoTask
from app.services import video_service

router = APIRouter()


@router.post(
    "/tasks",
    response_model=VideoTask,
    status_code=201,
    summary="提交视频生成任务（一次性返回完成态）",
)
async def create_task(
    payload: VideoCreateRequest, db: AsyncSession = Depends(get_db)
) -> VideoTask:
    try:
        return await video_service.create_task(db, payload.projectId)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/tasks/{task_id}", response_model=VideoTask, summary="查询任务状态")
async def get_task(
    task_id: str, db: AsyncSession = Depends(get_db)
) -> VideoTask:
    task = await video_service.get_task(db, task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="任务不存在")
    return task


@router.get("/{video_id}", response_model=VideoDetail, summary="视频详情")
async def get_video(
    video_id: str, db: AsyncSession = Depends(get_db)
) -> VideoDetail:
    video = await video_service.get_video(db, video_id)
    if video is None:
        raise HTTPException(status_code=404, detail="视频不存在")
    return video
