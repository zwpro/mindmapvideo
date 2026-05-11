"""AIGCDesk 客户端封装（Anthropic Messages API 协议）。

端点：POST {AIGCDESK_BASE_URL}/v1/messages
鉴权：Authorization: Bearer {AIGCDESK_API_KEY}

与原生 Anthropic API 的关键差异：
- system 提示放在顶层 `system` 字段，不允许出现在 messages 数组里。
- messages 角色仅限 user/assistant；本服务会自动把 system/developer 消息合并到顶层 system。
- max_tokens 是必填项，不传则默认 4096。
- 响应主体在 `content: [{type:"text", text}]`，没有 OpenAI 的 choices 结构。
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from typing import Any

import httpx
from fastapi import HTTPException, status

from app.core.config import settings
from app.schemas.chat import AIGCDeskChatRequest, ChatMessage

DEFAULT_MAX_TOKENS = 4096


class AIGCDeskAPIError(Exception):
    """AIGCDesk API 调用失败时抛出。"""

    def __init__(self, status_code: int, body: str) -> None:
        super().__init__(f"aigcdesk api error {status_code}: {body}")
        self.status_code = status_code
        self.body = body


def _to_anthropic_part(part: dict[str, Any]) -> dict[str, Any]:
    """ChatMessage.content 里的多模态片段 → Anthropic content block。

    支持方舟风格（input_text / input_image）与 OpenAI 风格（text / image_url）输入，
    统一翻译成 Anthropic 风格 {type:"text",text} / {type:"image",source:{type:"url",url}}。
    未识别类型原样透传。
    """
    t = part.get("type")
    if t in ("input_text", "output_text", "text"):
        return {"type": "text", "text": part.get("text", "")}
    if t in ("input_image", "image_url"):
        url = part.get("image_url") or ""
        return {"type": "image", "source": {"type": "url", "url": url}}
    return part


def _content_to_text(content: str | list[Any]) -> str:
    """把 ChatMessage.content（用作 system 时只取文本）压成单一字符串。"""
    if isinstance(content, str):
        return content
    parts: list[str] = []
    for c in content:
        data = c.model_dump() if hasattr(c, "model_dump") else c
        if not isinstance(data, dict):
            continue
        if data.get("type") in ("input_text", "output_text", "text"):
            text = data.get("text")
            if isinstance(text, str):
                parts.append(text)
    return "\n".join(parts)


def _message_to_anthropic(msg: ChatMessage) -> dict[str, Any]:
    """ChatMessage（user/assistant）→ Anthropic messages 数组项。"""
    if isinstance(msg.content, str):
        content: str | list[dict[str, Any]] = msg.content
    else:
        content = [
            _to_anthropic_part({k: v for k, v in part.model_dump().items() if v is not None})
            for part in msg.content
        ]
    return {"role": msg.role, "content": content}


def build_aigcdesk_payload(req: AIGCDeskChatRequest) -> dict[str, Any]:
    """AIGCDeskChatRequest → AIGCDESK /v1/messages 请求体（极简版）。

    AIGCDESK 中转对绝大多数可选字段都校验严格（temperature 已弃用、stream 触发
    SSE 路由、max_tokens 在部分模型上语义不一致等），按用户要求 payload 仅保留
    最小必须字段：``model`` + ``messages``。

    为不丢失语义，prompt 列表里的 system / developer 消息会被前置拼接到第一条
    user 消息内容里（带 ``[SYSTEM]`` 标记），而不是作为顶层 ``system`` 字段。
    """
    model = req.model or settings.AIGCDESK_MODEL
    if not model:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="未指定 model，且后端 AIGCDESK_MODEL 也未配置默认值",
        )

    system_parts: list[str] = []
    chat_msgs: list[dict[str, Any]] = []
    for m in req.messages:
        if m.role in ("system", "developer"):
            text = _content_to_text(m.content)
            if text:
                system_parts.append(text)
        else:
            chat_msgs.append(_message_to_anthropic(m))

    if not chat_msgs:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="messages 中至少需要一条 user/assistant 消息",
        )

    # 把 system 文本内联到第一条 user 消息前，避免直接丢失约束
    if system_parts:
        sys_text = "[SYSTEM]\n" + "\n\n".join(system_parts) + "\n\n[USER]\n"
        first = chat_msgs[0]
        if first["role"] == "user":
            content = first["content"]
            if isinstance(content, str):
                first["content"] = sys_text + content
            elif isinstance(content, list):
                first["content"] = [{"type": "text", "text": sys_text}, *content]

    return {"model": model, "messages": chat_msgs}


def _ensure_api_key(api_key_override: str | None = None) -> str:
    """显式传 api_key_override 时优先使用，便于上层用备用 key 重试。"""
    key = (api_key_override or settings.AIGCDESK_API_KEY or "").strip()
    if not key:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="AIGCDESK_API_KEY 未配置，请在 api/.env 中填入 AIGCDesk API Key",
        )
    return key


def _headers(api_key: str, *, stream: bool) -> dict[str, str]:
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        # AIGCDesk 作为 Anthropic 协议代理，部分实现会校验 anthropic-version。
        # 这里带上一个广泛兼容的版本号，多余时上游会忽略。
        "anthropic-version": "2023-06-01",
    }
    if stream:
        headers["Accept"] = "text/event-stream"
    return headers


def _extract_output_text(content: list[Any] | None) -> str:
    """Anthropic content list → 拼接所有 text 块。"""
    if not isinstance(content, list):
        return ""
    parts: list[str] = []
    for c in content:
        if isinstance(c, dict) and c.get("type") == "text":
            text = c.get("text")
            if isinstance(text, str):
                parts.append(text)
    return "".join(parts)


async def aigcdesk_chat(
    req: AIGCDeskChatRequest,
    *,
    api_key: str | None = None,
) -> dict[str, Any]:
    """非流式调用 /v1/messages，返回 Anthropic 响应（dict）。

    在原 response 上额外补一个 `output_text` 字段方便前端直接显示。
    传 ``api_key`` 可临时覆盖 settings.AIGCDESK_API_KEY，给上层做备用 key 重试用。
    """
    api_key = _ensure_api_key(api_key)
    payload = build_aigcdesk_payload(req)

    url = f"{settings.AIGCDESK_BASE_URL.rstrip('/')}/v1/messages"
    timeout = httpx.Timeout(settings.AIGCDESK_TIMEOUT_SECONDS, connect=15.0)
    async with httpx.AsyncClient(timeout=timeout) as client:
        resp = await client.post(url, json=payload, headers=_headers(api_key, stream=False))

    if resp.status_code >= 400:
        raise AIGCDeskAPIError(resp.status_code, resp.text)

    data: dict[str, Any] = resp.json()
    data.setdefault("output_text", _extract_output_text(data.get("content")))
    return data


async def aigcdesk_chat_stream(
    req: AIGCDeskChatRequest,
    *,
    api_key: str | None = None,
) -> AsyncIterator[bytes]:
    """流式调用 /v1/messages，按块 yield 原始 SSE 字节。

    Anthropic SSE 事件类型：message_start / content_block_start /
    content_block_delta / content_block_stop / message_delta / message_stop。
    本服务直接透传，前端按 Anthropic 事件协议消费即可。
    """
    api_key = _ensure_api_key(api_key)
    # 注：按"payload 仅保留 model+messages"的约束，这里也不再注入 stream=true。
    # 上游可能因此返回非 SSE 的整段 JSON，前端流式消费时需自行兜底。
    payload = build_aigcdesk_payload(req)

    url = f"{settings.AIGCDESK_BASE_URL.rstrip('/')}/v1/messages"
    timeout = httpx.Timeout(settings.AIGCDESK_TIMEOUT_SECONDS, connect=15.0)
    headers = _headers(api_key, stream=True)

    async with httpx.AsyncClient(timeout=timeout) as client:
        async with client.stream("POST", url, json=payload, headers=headers) as resp:
            if resp.status_code >= 400:
                body = (await resp.aread()).decode("utf-8", errors="replace")
                raise AIGCDeskAPIError(resp.status_code, body)
            async for chunk in resp.aiter_raw():
                if chunk:
                    yield chunk
