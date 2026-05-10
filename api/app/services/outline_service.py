"""分镜大纲生成服务。

主路径：调用火山引擎方舟 Responses API 走 LLM 生成。
回退路径：当 ARK_API_KEY 未配置或调用失败时使用本地模板，保证 Demo 不挂。
"""

from __future__ import annotations

import json
import logging
import re
from typing import Any

from nanoid import generate

from app.core.config import settings
from app.schemas.chat import ChatMessage, ChatRequest
from app.schemas.scene import Scene
from app.services import ark_service

logger = logging.getLogger(__name__)

GENERIC_SCENES: list[tuple[str, str]] = [
    ("开场引入", "用一段引人入胜的开场白带入主题，让观众迅速建立兴趣点。"),
    ("背景概述", "概括相关历史脉络与时代背景，帮助观众建立基础认知。"),
    ("核心概念", "拆解关键术语与定义，配合直观示例降低理解门槛。"),
    ("发展历程", "按时间线展示重要里程碑与关键人物，构建宏观视角。"),
    ("典型案例", "选取 1-2 个真实案例进行剖析，把理论落到具体场景中。"),
    ("挑战与争议", "客观呈现现存问题、争议与边界，引发更深入的思考。"),
    ("未来趋势", "结合最新动态与可信预测，展望未来 3-5 年的演进方向。"),
    ("总结回顾", "复盘全篇要点，留下一个值得收藏的观点或行动建议。"),
]

TOPIC_TEMPLATES: dict[str, list[tuple[str, str]]] = {
    "人工智能": [
        ("AI 的诞生", "1956 年达特茅斯会议正式提出『人工智能』概念，奠定研究方向。"),
        ("符号主义时代", "以专家系统为代表，依赖人工编码规则推演结论。"),
        ("机器学习兴起", "数据驱动取代规则编码，统计学习方法成为主流。"),
        ("深度学习突破", "AlexNet、ResNet 等架构推动图像与语音识别飞跃。"),
        ("大模型时代", "GPT、Claude 等基础模型展示通用智能的雏形。"),
        ("多模态融合", "文本、图像、视频、音频统一建模，能力跨模态迁移。"),
        ("未来与挑战", "对齐、安全、能耗、监管成为下一阶段核心议题。"),
    ],
}


SYSTEM_PROMPT = (
    "你是一位资深的科普视频脚本编辑，擅长把任意主题拆解成层次清晰、节奏明快的"
    "分镜叙事结构。要求每条分镜聚焦一个要点，按观看顺序排列，能让普通观众在 2-3 分钟内"
    "形成完整认知闭环。"
)

USER_PROMPT_TEMPLATE = (
    "请基于主题『{topic}』生成一份用于思维导图视频的分镜列表，要求：\n"
    "1. 输出 6-8 条分镜，按播放顺序排列；\n"
    "2. 每条分镜包含 title（不超过 12 字）与 content（30-60 字的旁白文本）；\n"
    "3. 整体覆盖：开场引入 → 关键概念/历程/案例 → 趋势或总结；\n"
    "4. 严格按以下 JSON 结构返回，不要包含任何额外文字、注释或 Markdown 代码块标记：\n"
    '{{"scenes":[{{"title":"...","content":"..."}}]}}'
)


def _pick_template(topic: str) -> list[tuple[str, str]]:
    for key, scenes in TOPIC_TEMPLATES.items():
        if key in topic:
            return scenes
    return GENERIC_SCENES


def _to_scenes(items: list[tuple[str, str]] | list[dict[str, Any]]) -> list[Scene]:
    out: list[Scene] = []
    for i, item in enumerate(items):
        if isinstance(item, tuple):
            title, content = item
            note: str | None = None
        else:
            title = str(item.get("title", "")).strip()
            content = str(item.get("content", "")).strip()
            raw_note = item.get("note")
            note = str(raw_note).strip() if raw_note else None
        if not title or not content:
            continue
        out.append(
            Scene(
                id=generate(size=10),
                index=i,
                title=title,
                content=content,
                note=note,
            )
        )
    return out


def generate_scenes_sync(topic: str) -> list[Scene]:
    """模板回退：不依赖外部服务，立即返回。"""
    return _to_scenes(_pick_template(topic))


_JSON_OBJECT_RE = re.compile(r"\{[\s\S]*\}")


def _parse_scenes_payload(text: str) -> list[dict[str, Any]] | None:
    """从模型回复里抽出 scenes 数组。

    优先把整段当 JSON 解析；失败时再从文本中提取首段 `{...}` 兜底。
    """
    if not text:
        return None

    candidates: list[str] = [text.strip()]
    match = _JSON_OBJECT_RE.search(text)
    if match:
        candidates.append(match.group(0))

    for candidate in candidates:
        try:
            data = json.loads(candidate)
        except json.JSONDecodeError:
            continue
        if isinstance(data, dict) and isinstance(data.get("scenes"), list):
            return [item for item in data["scenes"] if isinstance(item, dict)]
        if isinstance(data, list):
            return [item for item in data if isinstance(item, dict)]
    return None


async def generate_scenes_via_ark(topic: str) -> list[Scene] | None:
    """调用方舟 Responses API 生成分镜；失败返回 None 让上层回退。"""
    if not settings.ARK_API_KEY:
        return None

    req = ChatRequest(
        messages=[
            ChatMessage(role="system", content=SYSTEM_PROMPT),
            ChatMessage(role="user", content=USER_PROMPT_TEMPLATE.format(topic=topic)),
        ],
        temperature=0.7,
        max_output_tokens=1500,
        # 强制 JSON 格式输出，避免模型把 JSON 包在 ```json ... ``` 里
        extra={"text": {"format": {"type": "json_object"}}},
    )

    try:
        resp = await ark_service.ark_responses(req)
    except Exception as exc:  # noqa: BLE001
        logger.warning("ark generate scenes failed, fallback to template: %s", exc)
        return None

    output_text = str(resp.get("output_text") or "")
    items = _parse_scenes_payload(output_text)
    if not items:
        logger.warning(
            "ark scenes payload unparsable, raw=%s",
            output_text[:200].replace("\n", " "),
        )
        return None

    scenes = _to_scenes(items)
    return scenes or None


async def generate_scenes(topic: str) -> list[Scene]:
    """主入口：优先 LLM，失败回退本地模板。"""
    via_ark = await generate_scenes_via_ark(topic)
    if via_ark:
        return via_ark
    return generate_scenes_sync(topic)
