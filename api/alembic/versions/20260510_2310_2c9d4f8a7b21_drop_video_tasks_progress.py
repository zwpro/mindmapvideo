"""drop video_tasks.progress column

前端 ProgressPage 已改为纯轮询 stage 不展示进度数字，
后端不再需要 progress 列。stage 字段保留（state machine
仍依赖 voice/animation/compose/done/failed）。

Revision ID: 2c9d4f8a7b21
Revises: 1f3d2b9a4e10
Create Date: 2026-05-10 23:10:00+08:00
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "2c9d4f8a7b21"
down_revision: str | None = "1f3d2b9a4e10"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.drop_column("video_tasks", "progress")


def downgrade() -> None:
    op.add_column(
        "video_tasks",
        sa.Column(
            "progress",
            sa.Float(),
            nullable=False,
            server_default="0",
        ),
    )
