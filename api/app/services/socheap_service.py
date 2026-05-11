"""SoCheap 客户端封装（Anthropic Messages API 协议）。

定位：AIGCDesk 调用失败时的回退通道。协议与 aigcdesk_service.py 完全一致，
只是 base_url / api_key / model 走另一套配置，便于在两家中转间做主备切换。

端点：POST {SOCHEAP_BASE_URL}/v1/messages
鉴权：Authorization: Bearer {SOCHEAP_API_KEY}

与原生 Anthropic API 的关键差异（沿用 AIGCDesk 那边的约束，保持 payload 同构）：
- system 提示放在顶层 `system` 字段，不允许出现在 messages 数组里。
- messages 角色仅限 user/assistant；本服务会自动把 system/developer 消息合并到首条 user。
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


class SoCheapAPIError(Exception):
    """SoCheap API 调用失败时抛出。"""

    def __init__(self, status_code: int, body: str) -> None:
        super().__init__(f"socheap api error {status_code}: {body}")
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


def build_socheap_payload(req: AIGCDeskChatRequest) -> dict[str, Any]:
    """AIGCDeskChatRequest → SoCheap /v1/messages 请求体（与 AIGCDesk 同构的极简版）。

    payload 仅保留最小必须字段：``model`` + ``messages``。
    prompt 列表里的 system / developer 消息会被前置拼接到第一条 user 消息内容里
    （带 ``[SYSTEM]`` 标记），而不是作为顶层 ``system`` 字段。
    """
    model = req.model or settings.SOCHEAP_MODEL
    if not model:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="未指定 model，且后端 SOCHEAP_MODEL 也未配置默认值",
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


def _ensure_api_key() -> str:
    if not settings.SOCHEAP_API_KEY:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="SOCHEAP_API_KEY 未配置，请在 api/.env 中填入 SoCheap API Key",
        )
    return settings.SOCHEAP_API_KEY


def _headers(api_key: str, *, stream: bool) -> dict[str, str]:
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        # 与 AIGCDesk 一样，SoCheap 作为 Anthropic 协议代理，
        # 部分实现会校验 anthropic-version。带上一个广泛兼容的版本号，多余时上游会忽略。
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


async def socheap_chat(req: AIGCDeskChatRequest) -> dict[str, Any]:
    """非流式调用 /v1/messages，返回 Anthropic 响应（dict）。

    在原 response 上额外补一个 `output_text` 字段方便前端/上层直接显示。
    """
    api_key = _ensure_api_key()
    payload = build_socheap_payload(req)

    url = f"{settings.SOCHEAP_BASE_URL.rstrip('/')}/v1/messages"
    timeout = httpx.Timeout(settings.SOCHEAP_TIMEOUT_SECONDS, connect=15.0)
    async with httpx.AsyncClient(timeout=timeout) as client:
        resp = await client.post(url, json=payload, headers=_headers(api_key, stream=False))

    if resp.status_code >= 400:
        raise SoCheapAPIError(resp.status_code, resp.text)

    data: dict[str, Any] = resp.json()
    data.setdefault("output_text", _extract_output_text(data.get("content")))
    return data


async def socheap_chat_stream(req: AIGCDeskChatRequest) -> AsyncIterator[bytes]:
    """流式调用 /v1/messages，按块 yield 原始 SSE 字节。

    Anthropic SSE 事件类型：message_start / content_block_start /
    content_block_delta / content_block_stop / message_delta / message_stop。
    本服务直接透传，前端按 Anthropic 事件协议消费即可。
    """
    api_key = _ensure_api_key()
    payload = build_socheap_payload(req)

    url = f"{settings.SOCHEAP_BASE_URL.rstrip('/')}/v1/messages"
    timeout = httpx.Timeout(settings.SOCHEAP_TIMEOUT_SECONDS, connect=15.0)
    headers = _headers(api_key, stream=True)

    async with httpx.AsyncClient(timeout=timeout) as client:
        async with client.stream("POST", url, json=payload, headers=headers) as resp:
            if resp.status_code >= 400:
                body = (await resp.aread()).decode("utf-8", errors="replace")
                raise SoCheapAPIError(resp.status_code, body)
            async for chunk in resp.aiter_raw():
                if chunk:
                    yield chunk
