"""Project ORM。

对齐前端 Project DTO（src/types/index.ts）:
- 标量字段单独建列,便于查询/索引;
- outline / config 这种深嵌套结构存 JSON;
- scenes 走独立表 SceneORM。
"""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import JSON, DateTime, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base

if TYPE_CHECKING:
    from app.db.models.scene import SceneORM
    from app.db.models.video_task import VideoTaskORM


class ProjectORM(Base):
    __tablename__ = "projects"

    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    user_id: Mapped[str] = mapped_column(
        String(32), ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )

    topic: Mapped[str] = mapped_column(String(200), nullable=False)
    status: Mapped[str] = mapped_column(String(32), default="draft", nullable=False, index=True)
    thumbnail_url: Mapped[str] = mapped_column(String(512), default="", nullable=False)

    # 大纲与视频配置：嵌套结构整体存 JSON
    outline: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    config: Mapped[dict] = mapped_column(JSON, nullable=False)

    # 关联当前最新的 task / 已完成的 video（弱关联,允许为空）
    task_id: Mapped[str | None] = mapped_column(String(32), nullable=True)
    video_id: Mapped[str | None] = mapped_column(String(32), nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # 反向关系
    scenes: Mapped[list["SceneORM"]] = relationship(
        back_populates="project",
        cascade="all, delete-orphan",
        order_by="SceneORM.index",
    )
    tasks: Mapped[list["VideoTaskORM"]] = relationship(
        back_populates="project",
        cascade="all, delete-orphan",
        order_by="VideoTaskORM.started_at.desc()",
    )
