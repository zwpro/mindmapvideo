"""通用枚举，与前端 types/index.ts 同名。"""

from typing import Literal

ProjectStatus = Literal["draft", "generating", "completed", "failed"]
AnimationStyle = Literal["unfold", "roam", "focus", "overview"]
Resolution = Literal["720p", "1080p", "2k", "4k"]
Ratio = Literal["16:9", "9:16", "1:1"]
ThemeStyle = Literal["minimal", "tech", "academic", "cartoon", "business"]
GenerationStage = Literal["voice", "animation", "compose", "done", "failed"]
