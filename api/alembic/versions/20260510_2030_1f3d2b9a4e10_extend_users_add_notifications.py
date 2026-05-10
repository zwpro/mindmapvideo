"""extend users + add notifications + seed admin

给 users 表追加 avatar_url / bio / role 三列；新建 notifications 表；
插入一条 id='admin' 的种子用户，避免 projects.user_id 外键无主可指。

Revision ID: 1f3d2b9a4e10
Revises: dc031a9eb153
Create Date: 2026-05-10 20:30:00+08:00
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "1f3d2b9a4e10"
down_revision: str | None = "dc031a9eb153"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


ADMIN_AVATAR = (
    "https://trae-api-cn.mchost.guru/api/ide/v1/text_to_image"
    "?prompt=futuristic%20minimalist%20abstract%20avatar%20portrait"
    "%2C%20cyan%20glow%20highlights%2C%20deep%20navy%20background"
    "%2C%20geometric%20shapes&image_size=square"
)
ADMIN_BIO = "默认内置管理员，掌管全部本地项目空间。"


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column("avatar_url", sa.String(length=1024), nullable=False, server_default=""),
    )
    op.add_column(
        "users",
        sa.Column("bio", sa.String(length=512), nullable=False, server_default=""),
    )
    op.add_column(
        "users",
        sa.Column("role", sa.String(length=32), nullable=False, server_default="user"),
    )

    op.create_table(
        "notifications",
        sa.Column("id", sa.String(length=32), nullable=False),
        sa.Column("user_id", sa.String(length=32), nullable=False),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("level", sa.String(length=16), nullable=False, server_default="info"),
        sa.Column("link", sa.String(length=1024), nullable=True),
        sa.Column(
            "read",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("0"),
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_notifications_user_id"), "notifications", ["user_id"], unique=False
    )
    op.create_index(
        op.f("ix_notifications_created_at"), "notifications", ["created_at"], unique=False
    )

    # 种子 admin 用户
    users_table = sa.table(
        "users",
        sa.column("id", sa.String),
        sa.column("email", sa.String),
        sa.column("password_hash", sa.String),
        sa.column("nickname", sa.String),
        sa.column("avatar_url", sa.String),
        sa.column("bio", sa.String),
        sa.column("role", sa.String),
    )
    op.bulk_insert(
        users_table,
        [
            {
                "id": "admin",
                "email": "admin@local",
                "password_hash": "",
                "nickname": "Admin",
                "avatar_url": ADMIN_AVATAR,
                "bio": ADMIN_BIO,
                "role": "admin",
            }
        ],
    )


def downgrade() -> None:
    op.execute("DELETE FROM users WHERE id = 'admin'")

    op.drop_index(op.f("ix_notifications_created_at"), table_name="notifications")
    op.drop_index(op.f("ix_notifications_user_id"), table_name="notifications")
    op.drop_table("notifications")

    op.drop_column("users", "role")
    op.drop_column("users", "bio")
    op.drop_column("users", "avatar_url")
