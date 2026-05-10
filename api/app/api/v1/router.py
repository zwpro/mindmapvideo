"""v1 路由聚合。"""

from fastapi import APIRouter

from app.api.v1.endpoints import aigcdesk, chat, projects, scenes, users, videos

api_router = APIRouter()

api_router.include_router(projects.router, prefix="/projects", tags=["projects"])
api_router.include_router(scenes.router, prefix="/scenes", tags=["scenes"])
api_router.include_router(videos.router, prefix="/videos", tags=["videos"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(chat.router, prefix="/chat", tags=["chat"])
api_router.include_router(
    aigcdesk.router, prefix="/chat/aigcdesk", tags=["chat-aigcdesk"]
)
