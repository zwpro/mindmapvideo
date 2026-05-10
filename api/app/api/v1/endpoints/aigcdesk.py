"""AIGCDesk 对话端点（Anthropic Messages 协议）。

- POST /chat/aigcdesk/messages          非流式，返回完整 Anthropic message
- POST /chat/aigcdesk/messages/stream   流式，按 SSE 透传 Anthropic 事件
- GET  /chat/aigcdesk/health            检查 AIGCDESK_API_KEY 配置 & 默认模型
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

from app.core.config import settings
from app.schemas.chat import AIGCDeskChatRequest, AIGCDeskChatResponse
from app.services import aigcdesk_service
from app.services.aigcdesk_service import AIGCDeskAPIError

router = APIRouter()


@router.get("/health", summary="检查 AIGCDesk 接入配置")
async def aigcdesk_health() -> dict[str, object]:
    return {
        "configured": bool(settings.AIGCDESK_API_KEY),
        "base_url": settings.AIGCDESK_BASE_URL,
        "default_model": settings.AIGCDESK_MODEL or None,
    }


@router.post(
    "/messages",
    response_model=AIGCDeskChatResponse,
    summary="AIGCDesk 对话（非流式）",
    description="对接 AIGCDesk 的 Anthropic Messages 协议（POST /v1/messages）。"
    "后端注入 AIGCDESK_API_KEY，返回完整 response 并附 output_text 便利字段。",
)
async def aigcdesk_messages(payload: AIGCDeskChatRequest) -> AIGCDeskChatResponse:
    if payload.stream:
        raise HTTPException(
            status_code=400,
            detail="stream=true 请改用 /chat/aigcdesk/messages/stream 端点",
        )
    try:
        data = await aigcdesk_service.aigcdesk_chat(payload)
    except AIGCDeskAPIError as exc:
        raise HTTPException(
            status_code=502,
            detail={"upstream_status": exc.status_code, "upstream_body": exc.body},
        ) from exc
    return AIGCDeskChatResponse.model_validate(data)


@router.post(
    "/messages/stream",
    summary="AIGCDesk 对话（流式 SSE）",
    description="按 Server-Sent Events 透传上游 Anthropic 事件流（message_start / "
    "content_block_delta / message_stop 等），前端按 Anthropic 协议消费。",
)
async def aigcdesk_messages_stream(payload: AIGCDeskChatRequest) -> StreamingResponse:
    payload.stream = True

    async def _gen():
        try:
            async for chunk in aigcdesk_service.aigcdesk_chat_stream(payload):
                yield chunk
        except AIGCDeskAPIError as exc:
            # 透传上游错误为一条 error 事件
            yield (
                f"event: error\ndata: {{\"upstream_status\": {exc.status_code}, "
                f"\"upstream_body\": {exc.body!r}}}\n\n"
            ).encode("utf-8")

    headers = {
        "Cache-Control": "no-cache",
        "X-Accel-Buffering": "no",
        "Connection": "keep-alive",
    }
    return StreamingResponse(_gen(), media_type="text/event-stream", headers=headers)
