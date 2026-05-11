"""SQLAlchemy 异步会话与 ORM 基类。"""

from __future__ import annotations

from collections.abc import AsyncIterator

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

from app.core.config import settings


class Base(DeclarativeBase):
    pass


engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.APP_DEBUG,
    # 拿连接前先发一个轻量 ping。MySQL 默认 wait_timeout=28800s (8h)，
    # 加上托管层 / 代理层的 idle 杀连接策略，长跑的 worker 经常拿到 stale 连接
    # 触发 OperationalError 2006/2013 (server has gone away)。pre_ping 用一次往返
    # 换一次稳定性，对开发与生产都强烈推荐打开。
    pool_pre_ping=True,
    # 30 分钟主动回收一次连接，避开 MySQL / 中间件未通知客户端就 RST 的窗口。
    # 比 MySQL 默认 wait_timeout 短得多，永远不会和服务端的踢人时机撞上。
    pool_recycle=1800,
)
SessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def get_db() -> AsyncIterator[AsyncSession]:
    """FastAPI 依赖：每个请求一个 AsyncSession，结束后自动关闭。"""
    async with SessionLocal() as session:
        yield session
