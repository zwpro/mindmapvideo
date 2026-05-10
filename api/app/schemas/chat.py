"""对话（Chat）相关 schema。

对接火山引擎方舟 Responses API：
    POST https://ark.cn-beijing.volces.com/api/v3/responses

为前端提供「类 OpenAI Chat Completion」的简化语法（messages 数组），
后端在 service 层把 messages 翻译成方舟的 input 数组，再附带其它直通字段一起请求。

设计原则：
1. 简化常用字段（messages / model / stream / temperature / top_p / max_output_tokens / instructions / thinking）
2. 高级字段（tools / tool_choice / caching / store / previous_response_id 等）通过 extra 透传
3. 响应保留方舟 response object 原结构 + 额外提取一个 `output_text` 便于前端直接显示
"""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

ChatRole = Literal["system", "developer", "user", "assistant"]


class ChatTextPart(BaseModel):
    """input_text 内容元素。"""

    type: Literal["input_text", "output_text"] = "input_text"
    text: str


class ChatImagePart(BaseModel):
    """input_image 内容元素，二选一传入 file_id 或 image_url。"""

    type: Literal["input_image"] = "input_image"
    file_id: str | None = None
    image_url: str | None = None
    detail: Literal["low", "high", "xhigh"] | None = None


ChatContentPart = ChatTextPart | ChatImagePart


class ChatMessage(BaseModel):
    """单条对话消息，content 支持纯文本或多模态片段列表。"""

    role: ChatRole
    content: str | list[ChatContentPart]


class ThinkingConfig(BaseModel):
    type: Literal["enabled", "disabled", "auto"] = "disabled"


class ReasoningConfig(BaseModel):
    effort: Literal["minimal", "low", "medium", "high"] = "medium"


class ChatRequest(BaseModel):
    """前端发起对话的请求体。"""

    model_config = ConfigDict(extra="forbid")

    messages: list[ChatMessage] = Field(..., min_length=1)
    model: str | None = Field(
        default=None, description="不传则使用 settings.ARK_MODEL"
    )
    stream: bool = False
    temperature: float | None = Field(default=None, ge=0, le=2)
    top_p: float | None = Field(default=None, ge=0, le=1)
    max_output_tokens: int | None = Field(default=None, ge=1)
    instructions: str | None = None
    thinking: ThinkingConfig | None = None
    reasoning: ReasoningConfig | None = None

    # 透传给方舟 Responses API 的其它字段（tools / tool_choice / caching / store /
    # previous_response_id / include / context_management 等）。
    extra: dict[str, Any] | None = Field(
        default=None,
        description="原样合并到方舟请求体的额外字段，键名遵循方舟文档",
    )


class ChatUsage(BaseModel):
    model_config = ConfigDict(extra="allow")

    input_tokens: int | None = None
    output_tokens: int | None = None
    total_tokens: int | None = None


class ChatResponse(BaseModel):
    """非流式响应：方舟 response 原文 + 抽取的便利字段。"""

    model_config = ConfigDict(extra="allow")

    id: str | None = None
    model: str | None = None
    status: str | None = None
    output_text: str = Field(default="", description="拼接后的文本回答，便于前端直接显示")
    output: list[dict[str, Any]] = Field(default_factory=list, description="方舟 output 原数组")
    usage: ChatUsage | None = None


# ===== AIGCDesk（Anthropic Messages 协议） =====


class AIGCDeskChatRequest(BaseModel):
    """前端发起 AIGCDesk 对话的请求体。

    输入形状沿用 messages 数组（system 也可作为 message 项），
    服务层会把 system 消息从数组里摘出来放到 Anthropic 顶层 system 字段。
    """

    model_config = ConfigDict(extra="forbid")

    messages: list[ChatMessage] = Field(..., min_length=1)
    model: str | None = Field(
        default=None, description="不传则使用 settings.AIGCDESK_MODEL"
    )
    stream: bool = False
    temperature: float | None = Field(default=None, ge=0, le=2)
    top_p: float | None = Field(default=None, ge=0, le=1)
    max_tokens: int | None = Field(
        default=None,
        ge=1,
        description="Anthropic 必填；不传则后端默认 4096",
    )
    stop_sequences: list[str] | None = Field(
        default=None, description="Anthropic 风格停止序列"
    )

    # 透传到上游的其它字段（如 metadata / tools / tool_choice / system 块等）
    extra: dict[str, Any] | None = Field(
        default=None,
        description="原样合并到 /v1/messages 请求体的额外字段",
    )


class AIGCDeskContentBlock(BaseModel):
    model_config = ConfigDict(extra="allow")

    type: str
    text: str | None = None


class AIGCDeskUsage(BaseModel):
    model_config = ConfigDict(extra="allow")

    input_tokens: int | None = None
    output_tokens: int | None = None


class AIGCDeskChatResponse(BaseModel):
    """非流式响应：Anthropic /v1/messages 原文 + 便利字段。"""

    model_config = ConfigDict(extra="allow")

    id: str | None = None
    type: str | None = None
    role: str | None = None
    model: str | None = None
    content: list[AIGCDeskContentBlock] = Field(default_factory=list)
    stop_reason: str | None = None
    stop_sequence: str | None = None
    usage: AIGCDeskUsage | None = None
    output_text: str = Field(
        default="",
        description="把 content 里所有 text 块拼起来，便于前端直接显示",
    )
