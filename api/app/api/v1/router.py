"""v1 路由聚合。"""

from fastapi import APIRouter

from app.api.v1.endpoints import projects, scenes, videos

api_router = APIRouter()

api_router.include_router(projects.router, prefix="/projects", tags=["projects"])
api_router.include_router(scenes.router, prefix="/scenes", tags=["scenes"])
api_router.include_router(videos.router, prefix="/videos", tags=["videos"])
