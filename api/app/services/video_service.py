"""视频任务服务。

create_task 流程：
1. 同步在请求 session 里写一条 stage="voice" 的 VideoTaskORM 入库；
2. fire-and-forget 启动后台 video_pipeline.run_pipeline() 异步管线
   （LLM 生成 manim 脚本 → manim 渲染 → 抽缩略图 → 写 video_details）；
3. HTTP 立即返回 task DTO，前端通过轮询 /videos/tasks/{id} 拿到阶段切换。

进程重启会丢失正在跑的后台 pipeline（demo 限制），后续接 Celery 时把第 2 步
改成 .delay() / .send_task() 即可，DB 端的状态机保持不变。
"""

from __future__ import annotations

from datetime import datetime, timezone

from nanoid import generate
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.time_utils import to_utc_iso
from app.db.models import ProjectORM, VideoDetailORM, VideoTaskORM
from app.schemas.video import VideoDetail, VideoTask
from app.services import video_pipeline


def _orm_to_task(orm: VideoTaskORM) -> VideoTask:
    return VideoTask(
        id=orm.id,
        projectId=orm.project_id,
        stage=orm.stage,  # type: ignore[arg-type]
        startedAt=to_utc_iso(orm.started_at) or "",
        finishedAt=to_utc_iso(orm.finished_at),
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
        createdAt=to_utc_iso(orm.created_at) or "",
    )


async def create_task(db: AsyncSession, project_id: str) -> VideoTask:
    """创建任务：写一条初始 task 入库立即返回，真正合成在后台异步进行。

    - VideoDetailORM 不在这里写，等 pipeline 跑到 compose 阶段才会创建。
    - 任务最终态（done/failed）由 pipeline 自己更新。
    """
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
        stage="voice",
        error=None,
        video_id=video_id,
        started_at=now,
        finished_at=None,
    )
    db.add(task_orm)

    project.task_id = task_id
    project.video_id = video_id
    project.status = "generating"

    await db.commit()
    # 故意不 await db.refresh(task_orm)：
    # 1) session 配的是 expire_on_commit=False，commit 后属性不会被过期；
    # 2) 这条 task 的所有字段都是我们刚在代码里 set 的，没有 server_default 需要回读；
    # 3) 生产环境若有 MySQL 主从代理 / ProxySQL，refresh 的 SELECT 可能被路由到尚未同步
    #    的从库导致返回 0 行，触发 `Could not refresh instance` 让整个接口挂 500。

    # 调度后台流水线（fire-and-forget）。必须在 commit 之后再调度，
    # 否则后台任务可能比 task 行先抵达 DB，导致 _update_task 找不到记录。
    video_pipeline.schedule_pipeline(
        task_id=task_id, project_id=project_id, video_id=video_id
    )
    return _orm_to_task(task_orm)


async def get_task(db: AsyncSession, task_id: str) -> VideoTask | None:
    stmt = select(VideoTaskORM).where(VideoTaskORM.id == task_id)
    orm = (await db.execute(stmt)).scalar_one_or_none()
    return _orm_to_task(orm) if orm else None


async def get_video(db: AsyncSession, video_id: str) -> VideoDetail | None:
    stmt = select(VideoDetailORM).where(VideoDetailORM.id == video_id)
    orm = (await db.execute(stmt)).scalar_one_or_none()
    return _orm_to_video(orm) if orm else None
