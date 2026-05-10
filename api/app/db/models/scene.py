"""Scene ORM。

每个 Project 拥有 N 个 Scene,index 决定播放顺序。
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base

if TYPE_CHECKING:
    from app.db.models.project import ProjectORM


class SceneORM(Base):
    __tablename__ = "scenes"
    __table_args__ = (
        UniqueConstraint("project_id", "index", name="uq_scene_project_index"),
    )

    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    project_id: Mapped[str] = mapped_column(
        String(32), ForeignKey("projects.id", ondelete="CASCADE"), index=True, nullable=False
    )

    index: Mapped[int] = mapped_column(Integer, nullable=False)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    note: Mapped[str | None] = mapped_column(Text, nullable=True)

    project: Mapped["ProjectORM"] = relationship(back_populates="scenes")
