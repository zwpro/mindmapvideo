"""分镜（Scene）模型。

对齐前端 src/types/index.ts:
    interface Scene { id; index; title; content; note? }
"""

from pydantic import BaseModel, ConfigDict, Field


class Scene(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str = Field(..., description="分镜唯一 ID")
    index: int = Field(..., ge=0, description="在序列中的位置")
    title: str = Field(..., description="分镜标题")
    content: str = Field(..., description="分镜正文")
    note: str | None = Field(default=None, description="备注（可选）")


class SceneUpdate(BaseModel):
    title: str | None = None
    content: str | None = None
    note: str | None = None

