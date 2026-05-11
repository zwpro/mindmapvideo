"""视频配置 / 任务 / 详情模型。

对齐前端 src/types/index.ts:
    VideoConfig / VideoTask / VideoDetail
"""

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.common import (
    AnimationStyle,
    GenerationStage,
    Ratio,
    Resolution,
    ThemeStyle,
)


class VoiceConfig(BaseModel):
    id: str
    speed: float = 1.0
    volume: float = 1.0


class BgmConfig(BaseModel):
    id: str
    volume: float = 1.0


class VideoConfig(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    animationStyle: AnimationStyle = "unfold"
    resolution: Resolution = "720p"
    ratio: Ratio = "16:9"
    nodeDuration: int = Field(default=3, ge=1, le=20)
    voice: VoiceConfig | None = None
    bgm: BgmConfig | None = None
    theme: ThemeStyle = "minimal"


class VideoTask(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    projectId: str
    stage: GenerationStage
    startedAt: str
    finishedAt: str | None = None
    error: str | None = None
    videoId: str | None = None


class VideoDetail(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    projectId: str
    taskId: str
    url: str
    thumbnailUrl: str
    duration: float
    resolution: Resolution
    ratio: Ratio
    fileSize: int
    createdAt: str


class VideoCreateRequest(BaseModel):
    projectId: str

