"""项目（Project）模型。

对齐前端 src/types/index.ts:
    interface Project { id; userId; topic; status; thumbnailUrl;
                        outline; scenes; config; videoId?; taskId?;
                        createdAt; updatedAt; }
"""

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.common import ProjectStatus
from app.schemas.scene import Scene
from app.schemas.video import VideoConfig


class OutlineNode(BaseModel):
    id: str
    parentId: str | None
    title: str
    note: str | None = None
    depth: int
    children: list["OutlineNode"] = Field(default_factory=list)


OutlineNode.model_rebuild()


class Project(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    userId: str
    topic: str
    status: ProjectStatus
    thumbnailUrl: str
    outline: OutlineNode | None = None
    scenes: list[Scene] | None = None
    config: VideoConfig
    videoId: str | None = None
    taskId: str | None = None
    createdAt: str
    updatedAt: str


class ProjectCreate(BaseModel):
    topic: str = Field(..., min_length=1, max_length=200)


class ProjectUpdate(BaseModel):
    topic: str | None = None
    status: ProjectStatus | None = None
    thumbnailUrl: str | None = None
    outline: OutlineNode | None = None
    scenes: list[Scene] | None = None
    config: VideoConfig | None = None
    videoId: str | None = None
    taskId: str | None = None
