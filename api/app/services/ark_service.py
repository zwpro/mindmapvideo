"""火山引擎方舟 Responses API 客户端封装。

文档：https://www.volcengine.com/docs/82379/1958520
端点：POST {ARK_BASE_URL}/responses

职责：
1. 把前端「类 OpenAI Chat Completion」的 messages 翻译成方舟的 `input` 数组
2. 合并 model / 采样参数 / instructions / thinking / extra 等字段
3. 提供两种调用方式：
   - `ark_responses(payload)` 非流式，直接返回方舟 response object
   - `ark_responses_stream(payload)` 流式，按块 yield 原始 SSE 字节
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from typing import Any

import httpx
from fastapi import HTTPException, status

from app.core.config import settings
from app.schemas.chat import ChatMessage, ChatRequest


class ArkAPIError(Exception):
    """方舟 API 调用失败时抛出。"""

    def __init__(self, status_code: int, body: str) -> None:
        super().__init__(f"ark api error {status_code}: {body}")
        self.status_code = status_code
        self.body = body


def _message_to_input_item(msg: ChatMessage) -> dict[str, Any]:
    """单条 ChatMessage → 方舟 input 数组里的一项 message。

    方舟要求 message.content：
      - 文本：直接 string
      - 多模态：array of {type, text/image_url/...}
    我们这里：
      - content 是 str → 直接传字符串
      - content 是 list → 把每项 model_dump() 后过滤 None
    """
    if isinstance(msg.content, str):
        content: str | list[dict[str, Any]] = msg.content
    else:
        content = [
            {k: v for k, v in part.model_dump().items() if v is not None}
            for part in msg.content
        ]
    return {"type": "message", "role": msg.role, "content": content}


def build_ark_payload(req: ChatRequest) -> dict[str, Any]:
    """ChatRequest → 方舟 Responses API 请求体。"""
    payload: dict[str, Any] = {
        "model": req.model or settings.ARK_MODEL,
        "input": [_message_to_input_item(m) for m in req.messages],
        "stream": req.stream,
    }

    if req.temperature is not None:
        payload["temperature"] = req.temperature
    if req.top_p is not None:
        payload["top_p"] = req.top_p
    if req.max_output_tokens is not None:
        payload["max_output_tokens"] = req.max_output_tokens
    if req.instructions is not None:
        payload["instructions"] = req.instructions
    if req.thinking is not None:
        payload["thinking"] = req.thinking.model_dump()
    if req.reasoning is not None:
        payload["reasoning"] = req.reasoning.model_dump()
    if req.extra:
        for k, v in req.extra.items():
            payload.setdefault(k, v)
    return payload


def _ensure_api_key() -> str:
    if not settings.ARK_API_KEY:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="ARK_API_KEY 未配置，请在 api/.env 中填入火山引擎方舟 API Key",
        )
    return settings.ARK_API_KEY


def _headers(api_key: str, *, stream: bool) -> dict[str, str]:
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    if stream:
        headers["Accept"] = "text/event-stream"
    return headers


def _extract_output_text(output: list[dict[str, Any]]) -> str:
    """从方舟 response.output 数组里抽出 message > content[type=output_text].text 拼接。"""
    parts: list[str] = []
    for item in output:
        if item.get("type") != "message":
            continue
        for c in item.get("content") or []:
            if isinstance(c, dict) and c.get("type") == "output_text":
                text = c.get("text")
                if isinstance(text, str):
                    parts.append(text)
    return "".join(parts)


async def ark_responses(req: ChatRequest) -> dict[str, Any]:
    """非流式调用方舟 Responses API，返回方舟 response object（dict）。

    在原 response 上额外补一个 `output_text` 字段方便前端直接显示。
    """
    api_key = _ensure_api_key()
    payload = build_ark_payload(req)
    payload["stream"] = False

    url = f"{settings.ARK_BASE_URL.rstrip('/')}/responses"
    timeout = httpx.Timeout(settings.ARK_TIMEOUT_SECONDS, connect=15.0)
    async with httpx.AsyncClient(timeout=timeout) as client:
        resp = await client.post(url, json=payload, headers=_headers(api_key, stream=False))

    if resp.status_code >= 400:
        raise ArkAPIError(resp.status_code, resp.text)

    data: dict[str, Any] = resp.json()
    data.setdefault("output_text", _extract_output_text(data.get("output") or []))
    return data


async def ark_responses_stream(req: ChatRequest) -> AsyncIterator[bytes]:
    """流式调用方舟 Responses API，逐块 yield 原始 SSE 字节。

    上游已经是标准 SSE（`event: ...\\ndata: ...\\n\\n`），这里直接透传给前端，
    前端用 EventSource 或 fetch + ReadableStream 消费即可。
    """
    api_key = _ensure_api_key()
    payload = build_ark_payload(req)
    payload["stream"] = True

    url = f"{settings.ARK_BASE_URL.rstrip('/')}/responses"
    timeout = httpx.Timeout(settings.ARK_TIMEOUT_SECONDS, connect=15.0)
    headers = _headers(api_key, stream=True)

    async with httpx.AsyncClient(timeout=timeout) as client:
        async with client.stream("POST", url, json=payload, headers=headers) as resp:
            if resp.status_code >= 400:
                body = (await resp.aread()).decode("utf-8", errors="replace")
                raise ArkAPIError(resp.status_code, body)
            async for chunk in resp.aiter_raw():
                if chunk:
                    yield chunk
