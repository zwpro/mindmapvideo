"""用户与通知模型。

对齐前端 src/types/index.ts:
    interface AdminUser { id; nickname; avatarUrl; bio; role; }
    interface AppNotification { id; title; body; level; read; createdAt; link?; }
"""

from typing import Literal

from pydantic import BaseModel, ConfigDict


class AdminUser(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: Literal["admin"] = "admin"
    nickname: str
    avatarUrl: str
    bio: str
    role: Literal["admin"] = "admin"


class AdminUserUpdate(BaseModel):
    nickname: str | None = None
    avatarUrl: str | None = None
    bio: str | None = None


NotificationLevel = Literal["info", "success", "warning"]


class AppNotification(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    title: str
    body: str
    level: NotificationLevel
    read: bool
    createdAt: str
    link: str | None = None


class NotificationCreate(BaseModel):
    title: str
    body: str
    level: NotificationLevel = "info"
    link: str | None = None
