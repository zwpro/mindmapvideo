"""项目业务逻辑（SQLAlchemy 异步实现）。

所有读写都走 MySQL，通过 FastAPI Depends 注入的 AsyncSession 完成。
"""

from __future__ import annotations

from urllib.parse import quote

from nanoid import generate
from sqlalchemy import delete as sa_delete, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.time_utils import to_utc_iso
from app.db.models import ProjectORM, SceneORM
from app.schemas.project import OutlineNode, Project, ProjectCreate, ProjectUpdate
from app.schemas.scene import Scene
from app.schemas.video import VideoConfig

DEFAULT_USER_ID = "admin"
THUMBNAIL_BASE = "https://trae-api-cn.mchost.guru/api/ide/v1/text_to_image"


def build_thumbnail_url(topic: str) -> str:
    prompt = quote(f"{topic} 主题视觉封面，扁平插画风，简约几何元素，柔和渐变背景")
    return f"{THUMBNAIL_BASE}?prompt={prompt}&image_size=landscape_16_9"


def _orm_to_project(orm: ProjectORM, *, with_scenes: bool = False) -> Project:
    """ORM 实体 → Pydantic DTO（处理 snake_case ↔ camelCase 与 JSON 还原）。"""
    scenes: list[Scene] | None = None
    if with_scenes:
        loaded = list(orm.scenes) if orm.scenes is not None else []
        scenes = (
            [Scene.model_validate(s, from_attributes=True) for s in loaded]
            if loaded
            else None
        )

    outline = OutlineNode.model_validate(orm.outline) if orm.outline else None

    return Project(
        id=orm.id,
        userId=orm.user_id,
        topic=orm.topic,
        status=orm.status,  # type: ignore[arg-type]
        thumbnailUrl=orm.thumbnail_url,
        outline=outline,
        scenes=scenes,
        config=VideoConfig.model_validate(orm.config),
        videoId=orm.video_id,
        taskId=orm.task_id,
        createdAt=to_utc_iso(orm.created_at) or "",
        updatedAt=to_utc_iso(orm.updated_at) or "",
    )


async def list_projects(db: AsyncSession, user_id: str = DEFAULT_USER_ID) -> list[Project]:
    stmt = (
        select(ProjectORM)
        .where(ProjectORM.user_id == user_id)
        .order_by(ProjectORM.created_at.desc())
    )
    result = await db.execute(stmt)
    return [_orm_to_project(p, with_scenes=False) for p in result.scalars().all()]


async def get_project(db: AsyncSession, project_id: str) -> Project | None:
    stmt = (
        select(ProjectORM)
        .where(ProjectORM.id == project_id)
        .options(selectinload(ProjectORM.scenes))
    )
    result = await db.execute(stmt)
    orm = result.scalar_one_or_none()
    if orm is None:
        return None
    return _orm_to_project(orm, with_scenes=True)


async def create_project(
    db: AsyncSession, payload: ProjectCreate, user_id: str = DEFAULT_USER_ID
) -> Project:
    orm = ProjectORM(
        id=generate(size=10),
        user_id=user_id,
        topic=payload.topic,
        status="draft",
        thumbnail_url=build_thumbnail_url(payload.topic),
        outline=None,
        config=VideoConfig().model_dump(mode="json"),
        task_id=None,
        video_id=None,
    )
    db.add(orm)
    await db.commit()
    # 不 refresh：session=expire_on_commit=False，所有列都是 Python 端 set 的，
    # 生产 MySQL 主从/代理下 refresh 可能读不到刚写入行抛 InvalidRequestError。
    return _orm_to_project(orm, with_scenes=False)


async def update_project(
    db: AsyncSession, project_id: str, payload: ProjectUpdate
) -> Project | None:
    stmt = (
        select(ProjectORM)
        .where(ProjectORM.id == project_id)
        .options(selectinload(ProjectORM.scenes))
    )
    result = await db.execute(stmt)
    orm = result.scalar_one_or_none()
    if orm is None:
        return None

    patch = payload.model_dump(exclude_unset=True)

    if "topic" in patch and patch["topic"] is not None:
        orm.topic = patch["topic"]
    if "status" in patch and patch["status"] is not None:
        orm.status = patch["status"]
    if "thumbnailUrl" in patch and patch["thumbnailUrl"] is not None:
        orm.thumbnail_url = patch["thumbnailUrl"]
    if "outline" in patch:
        orm.outline = patch["outline"]  # 已经是 dict（exclude_unset 保证存在才赋值）
    if "config" in patch and patch["config"] is not None:
        orm.config = patch["config"]
    if "videoId" in patch:
        orm.video_id = patch["videoId"]
    if "taskId" in patch:
        orm.task_id = patch["taskId"]

    if "scenes" in patch:
        await db.execute(sa_delete(SceneORM).where(SceneORM.project_id == orm.id))
        new_scenes = patch["scenes"] or []
        for raw in new_scenes:
            db.add(
                SceneORM(
                    id=raw.get("id") or generate(size=10),
                    project_id=orm.id,
                    index=raw["index"],
                    title=raw["title"],
                    content=raw["content"],
                    note=raw.get("note"),
                )
            )

    await db.commit()
    # 标量列不需要 refresh：updated_at 走 Python 端 onupdate=utcnow，flush 时已贴到对象上，
    # session=expire_on_commit=False 也不会过期。生产 MySQL 主从代理下 refresh 还会偶发
    # 「读不到刚写入行」抛 InvalidRequestError。
    # 但 scenes 必须 refresh：上面 sa_delete + db.add 后内存里 orm.scenes 集合已脏，
    # 不重新加载会让响应里返回过期的分镜列表。
    await db.refresh(orm, attribute_names=["scenes"])
    return _orm_to_project(orm, with_scenes=True)


async def delete_project(db: AsyncSession, project_id: str) -> bool:
    stmt = select(ProjectORM).where(ProjectORM.id == project_id)
    result = await db.execute(stmt)
    orm = result.scalar_one_or_none()
    if orm is None:
        return False
    await db.delete(orm)
    await db.commit()
    return True
