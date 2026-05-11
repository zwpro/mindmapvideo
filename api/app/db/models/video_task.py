"""VideoTask ORM。

记录一次视频生成任务的状态机：voice -> animation -> compose -> done/failed。
"""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.time_utils import utcnow
from app.db.session import Base

if TYPE_CHECKING:
    from app.db.models.project import ProjectORM


class VideoTaskORM(Base):
    __tablename__ = "video_tasks"

    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    project_id: Mapped[str] = mapped_column(
        String(32), ForeignKey("projects.id", ondelete="CASCADE"), index=True, nullable=False
    )

    stage: Mapped[str] = mapped_column(String(32), default="voice", nullable=False, index=True)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    video_id: Mapped[str | None] = mapped_column(String(32), nullable=True)

    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, nullable=False
    )
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    project: Mapped["ProjectORM"] = relationship(back_populates="tasks")
