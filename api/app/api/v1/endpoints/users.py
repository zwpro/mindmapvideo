"""用户与通知端点。"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.schemas.user import (
    AdminUser,
    AdminUserUpdate,
    AppNotification,
    NotificationCreate,
)
from app.services import user_service

router = APIRouter()


@router.get("/me", response_model=AdminUser, summary="当前用户信息")
async def get_me(db: AsyncSession = Depends(get_db)) -> AdminUser:
    return await user_service.get_me(db)


@router.patch("/me", response_model=AdminUser, summary="更新当前用户")
async def update_me(
    payload: AdminUserUpdate, db: AsyncSession = Depends(get_db)
) -> AdminUser:
    return await user_service.update_me(db, payload)


@router.get(
    "/me/notifications",
    response_model=list[AppNotification],
    summary="通知列表",
)
async def list_notifications(
    db: AsyncSession = Depends(get_db),
) -> list[AppNotification]:
    return await user_service.list_notifications(db)


@router.post(
    "/me/notifications",
    response_model=AppNotification,
    status_code=status.HTTP_201_CREATED,
    summary="新增通知（mock 调试用）",
)
async def push_notification(
    payload: NotificationCreate, db: AsyncSession = Depends(get_db)
) -> AppNotification:
    return await user_service.push_notification(db, payload)


@router.post(
    "/me/notifications/{notification_id}/read",
    response_model=AppNotification,
    summary="标记通知已读",
)
async def mark_read(
    notification_id: str, db: AsyncSession = Depends(get_db)
) -> AppNotification:
    item = await user_service.mark_read(db, notification_id)
    if item is None:
        raise HTTPException(status_code=404, detail="通知不存在")
    return item


@router.post(
    "/me/notifications/read-all",
    summary="全部已读",
)
async def mark_all_read(db: AsyncSession = Depends(get_db)) -> dict[str, int]:
    return {"updated": await user_service.mark_all_read(db)}
