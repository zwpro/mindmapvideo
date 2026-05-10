"""视频合成服务（mock）。

当前同步生成视频结果。后续接 Celery + MoviePy/FFmpeg 真实合成。
"""

from __future__ import annotations

from datetime import datetime, timezone

from nanoid import generate

from app.schemas.video import VideoDetail, VideoTask

# 内存任务表（上线时换成 DB + Redis）
_tasks: dict[str, VideoTask] = {}
_videos: dict[str, VideoDetail] = {}


def now_iso() -> str:
    return datetime.now(tz=timezone.utc).isoformat()


def create_task(project_id: str) -> VideoTask:
    task_id = generate(size=12)
    video_id = generate(size=12)
    started = now_iso()

    video = VideoDetail(
        id=video_id,
        projectId=project_id,
        taskId=task_id,
        url=f"/media/{video_id}.mp4",
        thumbnailUrl=f"/media/{video_id}.jpg",
        duration=120.0,
        resolution="720p",
        ratio="16:9",
        fileSize=15 * 1024 * 1024,
        createdAt=started,
    )
    _videos[video_id] = video

    task = VideoTask(
        id=task_id,
        projectId=project_id,
        stage="done",
        progress=1.0,
        startedAt=started,
        finishedAt=now_iso(),
        videoId=video_id,
    )
    _tasks[task_id] = task
    return task


def get_task(task_id: str) -> VideoTask | None:
    return _tasks.get(task_id)


def get_video(video_id: str) -> VideoDetail | None:
    return _videos.get(video_id)
