"""视频任务服务（SQLAlchemy 异步实现，mock 一次性完成态）。

当前接收任务后立即写入 video_tasks 与 video_details 两张表，并把
project.task_id / video_id / status 同步落库；后续接 Celery + FFmpeg 时，
create_task 改为入队，由 worker 多次更新 video_tasks.stage / progress 即可。
"""

from __future__ import annotations

from datetime import datetime, timezone

from nanoid import generate
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import ProjectORM, VideoDetailORM, VideoTaskORM
from app.schemas.video import VideoDetail, VideoTask


def _orm_to_task(orm: VideoTaskORM) -> VideoTask:
    return VideoTask(
        id=orm.id,
        projectId=orm.project_id,
        stage=orm.stage,  # type: ignore[arg-type]
        progress=orm.progress,
        startedAt=orm.started_at.isoformat(),
        finishedAt=orm.finished_at.isoformat() if orm.finished_at else None,
        error=orm.error,
        videoId=orm.video_id,
    )


def _orm_to_video(orm: VideoDetailORM) -> VideoDetail:
    return VideoDetail(
        id=orm.id,
        projectId=orm.project_id,
        taskId=orm.task_id or "",
        url=orm.url,
        thumbnailUrl=orm.thumbnail_url,
        duration=orm.duration,
        resolution=orm.resolution,  # type: ignore[arg-type]
        ratio=orm.ratio,  # type: ignore[arg-type]
        fileSize=orm.file_size,
        createdAt=orm.created_at.isoformat(),
    )


async def create_task(db: AsyncSession, project_id: str) -> VideoTask:
    """创建任务并立即合成出视频（mock）。"""
    project_stmt = select(ProjectORM).where(ProjectORM.id == project_id)
    project = (await db.execute(project_stmt)).scalar_one_or_none()
    if project is None:
        raise ValueError(f"project not found: {project_id}")

    task_id = generate(size=12)
    video_id = generate(size=12)
    now = datetime.now(tz=timezone.utc)

    task_orm = VideoTaskORM(
        id=task_id,
        project_id=project_id,
        stage="done",
        progress=1.0,
        error=None,
        video_id=video_id,
        started_at=now,
        finished_at=now,
    )
    video_orm = VideoDetailORM(
        id=video_id,
        project_id=project_id,
        task_id=task_id,
        url=f"/media/{video_id}.mp4",
        thumbnail_url=f"/media/{video_id}.jpg",
        duration=120.0,
        resolution="720p",
        ratio="16:9",
        file_size=15 * 1024 * 1024,
        created_at=now,
    )

    # video_details.task_id 外键指向 video_tasks，需要保证 task 先落库；
    # 这里用一次显式 flush 控制插入顺序，避免 UoW 把 video_details 排在前面。
    db.add(task_orm)
    await db.flush()
    db.add(video_orm)

    project.task_id = task_id
    project.video_id = video_id
    project.status = "completed"

    await db.commit()
    await db.refresh(task_orm)
    return _orm_to_task(task_orm)


async def get_task(db: AsyncSession, task_id: str) -> VideoTask | None:
    stmt = select(VideoTaskORM).where(VideoTaskORM.id == task_id)
    orm = (await db.execute(stmt)).scalar_one_or_none()
    return _orm_to_task(orm) if orm else None


async def get_video(db: AsyncSession, video_id: str) -> VideoDetail | None:
    stmt = select(VideoDetailORM).where(VideoDetailORM.id == video_id)
    orm = (await db.execute(stmt)).scalar_one_or_none()
    return _orm_to_video(orm) if orm else None
