"""FastAPI 应用入口。"""

from contextlib import asynccontextmanager
from collections.abc import AsyncIterator
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app import __version__
from app.api.v1.router import api_router
from app.core.config import settings


def _ensure_media_dirs() -> Path:
    """创建 media 根目录与三类子目录（脚本/视频/缩略图）。返回绝对路径。"""
    root = Path(settings.MEDIA_ROOT).resolve()
    for sub in ("scripts", "videos", "thumbnails"):
        (root / sub).mkdir(parents=True, exist_ok=True)
    return root


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    # 启动时：初始化数据库、Redis、LLM client 等
    _ensure_media_dirs()
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
