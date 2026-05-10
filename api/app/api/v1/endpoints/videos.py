"""视频任务端点。"""

from fastapi import APIRouter, HTTPException

from app.schemas.video import VideoCreateRequest, VideoDetail, VideoTask
from app.services import video_service

router = APIRouter()


@router.post(
    "/tasks",
    response_model=VideoTask,
    status_code=201,
    summary="提交视频生成任务",
)
async def create_task(payload: VideoCreateRequest) -> VideoTask:
    return video_service.create_task(payload.projectId)


@router.get("/tasks/{task_id}", response_model=VideoTask, summary="查询任务状态")
async def get_task(task_id: str) -> VideoTask:
    task = video_service.get_task(task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="任务不存在")
    return task


@router.get("/{video_id}", response_model=VideoDetail, summary="视频详情")
async def get_video(video_id: str) -> VideoDetail:
    video = video_service.get_video(video_id)
    if video is None:
        raise HTTPException(status_code=404, detail="视频不存在")
    return video
