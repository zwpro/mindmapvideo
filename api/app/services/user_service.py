"""用户与通知服务（SQLAlchemy 异步实现）。

当前系统单租户，固定用 id='admin'（由迁移种子）。所有读写都落 MySQL。
"""

from __future__ import annotations

from datetime import datetime, timezone

from nanoid import generate
from sqlalchemy import select, update as sa_update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.time_utils import to_utc_iso
from app.db.models import NotificationORM, UserORM
from app.schemas.user import (
    AdminUser,
    AdminUserUpdate,
    AppNotification,
    NotificationCreate,
)

ADMIN_ID = "admin"


def _orm_to_user(orm: UserORM) -> AdminUser:
    return AdminUser(
        id="admin",
        nickname=orm.nickname or "Admin",
        avatarUrl=orm.avatar_url,
        bio=orm.bio,
        role="admin",
    )


def _orm_to_notification(orm: NotificationORM) -> AppNotification:
    return AppNotification(
        id=orm.id,
        title=orm.title,
        body=orm.body,
        level=orm.level,  # type: ignore[arg-type]
        read=orm.read,
        createdAt=to_utc_iso(orm.created_at) or "",
        link=orm.link,
    )


async def _get_admin_orm(db: AsyncSession) -> UserORM:
    stmt = select(UserORM).where(UserORM.id == ADMIN_ID)
    orm = (await db.execute(stmt)).scalar_one_or_none()
    if orm is None:
        raise RuntimeError(
            "admin 用户不存在，请先执行 alembic upgrade head 初始化种子数据"
        )
    return orm


async def get_me(db: AsyncSession) -> AdminUser:
    return _orm_to_user(await _get_admin_orm(db))


async def update_me(db: AsyncSession, payload: AdminUserUpdate) -> AdminUser:
    orm = await _get_admin_orm(db)
    patch = payload.model_dump(exclude_unset=True)
    if "nickname" in patch and patch["nickname"] is not None:
        orm.nickname = patch["nickname"]
    if "avatarUrl" in patch and patch["avatarUrl"] is not None:
        orm.avatar_url = patch["avatarUrl"]
    if "bio" in patch and patch["bio"] is not None:
        orm.bio = patch["bio"]
    await db.commit()
    await db.refresh(orm)
    return _orm_to_user(orm)


async def list_notifications(db: AsyncSession) -> list[AppNotification]:
    stmt = (
        select(NotificationORM)
        .where(NotificationORM.user_id == ADMIN_ID)
        .order_by(NotificationORM.created_at.desc())
    )
    rows = (await db.execute(stmt)).scalars().all()
    return [_orm_to_notification(r) for r in rows]


async def push_notification(
    db: AsyncSession, payload: NotificationCreate
) -> AppNotification:
    orm = NotificationORM(
        id=f"n-{generate(size=10)}",
        user_id=ADMIN_ID,
        title=payload.title,
        body=payload.body,
        level=payload.level,
        link=payload.link,
        read=False,
        created_at=datetime.now(tz=timezone.utc),
    )
    db.add(orm)
    await db.commit()
    await db.refresh(orm)
    return _orm_to_notification(orm)


async def mark_read(db: AsyncSession, notification_id: str) -> AppNotification | None:
    stmt = select(NotificationORM).where(
        NotificationORM.id == notification_id,
        NotificationORM.user_id == ADMIN_ID,
    )
    orm = (await db.execute(stmt)).scalar_one_or_none()
    if orm is None:
        return None
    orm.read = True
    await db.commit()
    await db.refresh(orm)
    return _orm_to_notification(orm)


async def mark_all_read(db: AsyncSession) -> int:
    stmt = (
        sa_update(NotificationORM)
        .where(
            NotificationORM.user_id == ADMIN_ID,
            NotificationORM.read.is_(False),
        )
        .values(read=True)
        .execution_options(synchronize_session=False)
    )
    result = await db.execute(stmt)
    await db.commit()
    return int(result.rowcount or 0)
