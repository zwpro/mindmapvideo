"""把历史 server_default=func.now() 写入的本地时间统一转回 UTC

历史背景：
- MySQL 服务器时区为 SYSTEM（=+08:00），过去 ORM 用 server_default=func.now()
  写入 created_at/updated_at，存进 DB 的是 +8 北京时间；
- 但 Python 代码侧的 datetime.now(tz=timezone.utc) 写入是 UTC；
- 这次把所有 ORM 切到 client-side default=utcnow 后，新数据全部 UTC。
- 旧数据需要回填：projects / users 表里所有时间整体减 8 小时；
- notifications 表早期 +8、最近 UTC 混杂，且都是测试数据，直接清空避免歧义。
- video_tasks / video_details / scenes 一直是 Python UTC 写入，保持不动。

Revision ID: 3e8f2d7c5b94
Revises: 2c9d4f8a7b21
Create Date: 2026-05-11 11:35:00+08:00
"""

from __future__ import annotations

from collections.abc import Sequence

from alembic import op

revision: str = "3e8f2d7c5b94"
down_revision: str | None = "2c9d4f8a7b21"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # projects: 全部时间字段 -8h
    op.execute(
        "UPDATE projects SET "
        "  created_at = DATE_SUB(created_at, INTERVAL 8 HOUR), "
        "  updated_at = DATE_SUB(updated_at, INTERVAL 8 HOUR)"
    )

    # users: 全部时间字段 -8h（admin 种子用户也是 +8 写入的）
    op.execute(
        "UPDATE users SET "
        "  created_at = DATE_SUB(created_at, INTERVAL 8 HOUR), "
        "  updated_at = DATE_SUB(updated_at, INTERVAL 8 HOUR)"
    )

    # notifications: 早期 +8 / 近期 UTC 混杂，且都是开发期测试通知，整表清空
    op.execute("DELETE FROM notifications")


def downgrade() -> None:
    # 数据回滚仅尽力还原 projects/users 的时间漂移，notifications 无法恢复
    op.execute(
        "UPDATE projects SET "
        "  created_at = DATE_ADD(created_at, INTERVAL 8 HOUR), "
        "  updated_at = DATE_ADD(updated_at, INTERVAL 8 HOUR)"
    )
    op.execute(
        "UPDATE users SET "
        "  created_at = DATE_ADD(created_at, INTERVAL 8 HOUR), "
        "  updated_at = DATE_ADD(updated_at, INTERVAL 8 HOUR)"
    )
