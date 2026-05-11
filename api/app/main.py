"""FastAPI 应用入口。"""

import logging
from contextlib import asynccontextmanager
from collections.abc import AsyncIterator
from datetime import datetime, timedelta, timezone
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy import select, update

from app import __version__
from app.api.v1.router import api_router
from app.core.config import settings
from app.db.models import VideoTaskORM
from app.db.session import SessionLocal

logger = logging.getLogger(__name__)


def _ensure_media_dirs() -> Path:
    """创建 media 根目录与三类子目录（脚本/视频/缩略图）。返回绝对路径。"""
    root = Path(settings.MEDIA_ROOT).resolve()
    for sub in ("scripts", "videos", "thumbnails"):
        (root / sub).mkdir(parents=True, exist_ok=True)
    return root


# 中间态字面量。
_PENDING_STAGES = ("voice", "animation", "compose")
# 启动清理阈值：只有 started_at 早于 (now - STUCK_THRESHOLD) 的中间态 task 才会被
# 标 failed。pipeline 现在跑在 detached 子进程里（见 video_pipeline.schedule_pipeline），
# uvicorn worker 重启不会影响它，所以正在跑的 task 不能被误杀。
# manim 单次渲染上限 5min，加上 LLM/compose 一般 < 8min，30 min 阈值足够宽。
STUCK_THRESHOLD = timedelta(minutes=30)


async def _cleanup_stuck_tasks() -> None:
    """启动清理：把「上次启动后明显死掉」的中间态 task 标记为 failed。

    判定条件（必须全部满足）：
      1. stage ∈ (voice, animation, compose)
      2. finished_at IS NULL
      3. started_at 早于 now - STUCK_THRESHOLD（默认 30 分钟）

    第 3 条是 v2 detached pipeline 的关键约束：detached 子进程可能此刻还在
    渲染，不能因为 uvicorn worker 重启就把它的 task 标 failed。30 分钟
    阈值远大于任何合理 pipeline 时长，凡是超过这个阈值仍在中间态的，
    99% 是上次崩溃的残余。
    """
    threshold = datetime.now(tz=timezone.utc) - STUCK_THRESHOLD
    async with SessionLocal() as db:
        stmt = select(VideoTaskORM).where(
            VideoTaskORM.stage.in_(_PENDING_STAGES),
            VideoTaskORM.finished_at.is_(None),
            VideoTaskORM.started_at < threshold,
        )
        stuck = (await db.execute(stmt)).scalars().all()
        if not stuck:
            return
        ids = [t.id for t in stuck]
        await db.execute(
            update(VideoTaskORM)
            .where(VideoTaskORM.id.in_(ids))
            .values(
                stage="failed",
                error="任务超过 30 分钟仍未完成，已自动收尾。请重新提交生成。",
                finished_at=datetime.now(tz=timezone.utc),
            )
        )
        await db.commit()
        logger.warning("startup cleanup: marked %d stuck task(s) as failed: %s", len(ids), ids)


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    # 启动时：初始化目录 + 收尾上次留下的 stuck task
    _ensure_media_dirs()
    try:
        await _cleanup_stuck_tasks()
    except Exception:  # noqa: BLE001 — 清理失败不该阻塞服务起飞
        logger.exception("startup cleanup_stuck_tasks failed (non-fatal)")
    yield
    # 关闭时：优雅释放


def create_app() -> FastAPI:
    app = FastAPI(
        title="Mindmap API",
        version=__version__,
        description="一句话生成思维导图视频的后端服务",
        lifespan=lifespan,
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(api_router, prefix="/api/v1")

    media_root = _ensure_media_dirs()
    app.mount("/media", StaticFiles(directory=str(media_root)), name="media")

    @app.get("/health", tags=["meta"])
    async def health() -> dict[str, str]:
        return {"status": "ok", "version": __version__, "env": settings.APP_ENV}

    return app


app = create_app()
