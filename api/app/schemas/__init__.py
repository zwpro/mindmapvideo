"""Pydantic schemas，对齐前端 src/types/index.ts。"""

from app.schemas.common import (
    AnimationStyle,
    GenerationStage,
    ProjectStatus,
    Ratio,
    Resolution,
    ThemeStyle,
)
from app.schemas.project import (
    Project,
    ProjectCreate,
    ProjectUpdate,
)
from app.schemas.scene import (
    Scene,
    SceneUpdate,
)
from app.schemas.video import (
    VideoConfig,
    VideoDetail,
    VideoTask,
)

__all__ = [
    "AnimationStyle",
    "GenerationStage",
    "Project",
    "ProjectCreate",
    "ProjectStatus",
    "ProjectUpdate",
    "Ratio",
    "Resolution",
    "Scene",
    "SceneUpdate",
    "ThemeStyle",
    "VideoConfig",
    "VideoDetail",
    "VideoTask",
]
