"""分镜生成服务。

当前提供 mock 实现，后续接入真实 LLM（OpenAI / Claude）。
"""

from __future__ import annotations

from nanoid import generate

from app.schemas.scene import Scene

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


def _pick_template(topic: str) -> list[tuple[str, str]]:
    for key, scenes in TOPIC_TEMPLATES.items():
        if key in topic:
            return scenes
    return GENERIC_SCENES


def generate_scenes_sync(topic: str) -> list[Scene]:
    """同步生成完整分镜列表（用于测试/兜底）。"""
    raw = _pick_template(topic)
    return [
        Scene(id=generate(size=10), index=i, title=title, content=content)
        for i, (title, content) in enumerate(raw)
    ]
