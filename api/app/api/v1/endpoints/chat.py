"""对话端点：对接火山引擎方舟 Responses API。

- POST /chat/responses        非流式，返回完整 response object
- POST /chat/responses/stream 流式，按 SSE 透传方舟事件流
- GET  /chat/health           检查 ARK_API_KEY 配置 & 默认模型
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

from app.core.config import settings
from app.schemas.chat import ChatRequest, ChatResponse
from app.services import ark_service
from app.services.ark_service import ArkAPIError

router = APIRouter()


@router.get("/health", summary="检查方舟接入配置")
async def chat_health() -> dict[str, object]:
    return {
        "configured": bool(settings.ARK_API_KEY),
        "base_url": settings.ARK_BASE_URL,
        "default_model": settings.ARK_MODEL,
    }


@router.post(
    "/responses",
    response_model=ChatResponse,
    summary="对话（非流式）",
    description="将 messages 翻译为方舟 Responses API 的 input 数组，"
    "调用后端 ARK_API_KEY 一次性返回完整结果，并附 output_text 便利字段。",
)
async def chat_responses(payload: ChatRequest) -> ChatResponse:
    if payload.stream:
        raise HTTPException(
            status_code=400,
            detail="stream=true 请改用 /chat/responses/stream 端点",
        )
    try:
        data = await ark_service.ark_responses(payload)
    except ArkAPIError as exc:
        raise HTTPException(
            status_code=502,
            detail={"upstream_status": exc.status_code, "upstream_body": exc.body},
        ) from exc
    return ChatResponse.model_validate(data)


@router.post(
    "/responses/stream",
    summary="对话（流式 SSE）",
    description="按 Server-Sent Events 透传方舟原始事件流（event/data 行）。"
    "前端用 EventSource 或 fetch + ReadableStream 消费，最终以 `data: [DONE]` 结束。",
)
async def chat_responses_stream(payload: ChatRequest) -> StreamingResponse:
    payload.stream = True

    async def _gen():
        try:
            async for chunk in ark_service.ark_responses_stream(payload):
                yield chunk
        except ArkAPIError as exc:
            # 透传上游错误为一条 error 事件（保持 SSE 协议合法）
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
