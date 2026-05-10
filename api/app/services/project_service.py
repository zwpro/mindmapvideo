"""项目业务逻辑（mock 内存实现）。"""

from __future__ import annotations

from datetime import datetime, timezone

from nanoid import generate

from app.schemas.project import Project, ProjectCreate, ProjectUpdate
from app.schemas.video import VideoConfig

_projects: dict[str, Project] = {}


def now_iso() -> str:
    return datetime.now(tz=timezone.utc).isoformat()


def list_projects(user_id: str = "admin") -> list[Project]:
    return [p for p in _projects.values() if p.userId == user_id]


def get_project(project_id: str) -> Project | None:
    return _projects.get(project_id)


def create_project(payload: ProjectCreate, user_id: str = "admin") -> Project:
    project = Project(
        id=generate(size=10),
        userId=user_id,
        topic=payload.topic,
        status="draft",
        thumbnailUrl="",
        outline=None,
        scenes=None,
        config=VideoConfig(),
        createdAt=now_iso(),
        updatedAt=now_iso(),
    )
    _projects[project.id] = project
    return project


def update_project(project_id: str, payload: ProjectUpdate) -> Project | None:
    project = _projects.get(project_id)
    if project is None:
        return None
    data = project.model_dump()
    patch = payload.model_dump(exclude_unset=True)
    data.update(patch)
    data["updatedAt"] = now_iso()
    new_project = Project.model_validate(data)
    _projects[project_id] = new_project
    return new_project


def delete_project(project_id: str) -> bool:
    return _projects.pop(project_id, None) is not None
