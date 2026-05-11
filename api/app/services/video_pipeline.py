"""视频合成流水线：调 AIGCDESK 生成 manim 脚本 → 落盘 → manim 渲染 → 写库。

阶段映射（沿用 schemas.common.GenerationStage 字面量，不破坏前端契约）：
    voice     → 调 LLM 生成 manim 脚本（0%~100%）
    animation → 跑 manim 子进程渲染（0%~100%）
    compose   → 移动产物、抽缩略图、写 video_details（0%~100%）
    done      → 全流程完成
    failed    → 任意阶段抛错，error 字段记录原因

后台调度：HTTP create_task 处理函数立即写一条 stage=voice 的 task 入库后返回，
另起 asyncio.create_task() 跑本模块 run_pipeline()。
进程重启会丢失正在跑的任务（demo 限制），后续接 Celery 时本模块的 run_pipeline()
也可作为 worker 入口直接复用。
"""

from __future__ import annotations

import asyncio
import logging
import re
import shutil
import subprocess  # noqa: S404 — 需要常量
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from sqlalchemy import select

from app.core.config import settings
from app.db.models import ProjectORM, SceneORM, VideoDetailORM, VideoTaskORM
from app.db.session import SessionLocal
from app.schemas.chat import AIGCDeskChatRequest, ChatMessage
from app.services import aigcdesk_service
from app.services.aigcdesk_service import AIGCDeskAPIError

logger = logging.getLogger(__name__)

MANIM_TIMEOUT_SECONDS = 300  # manim 渲染超时上限
SCENE_CLASS_NAME = "MainScene"
DEFAULT_QUALITY_FLAG = "-qm"  # 720p30
DEFAULT_QUALITY_DIR = "720p30"


# ---------- LLM Prompt ----------

SYSTEM_PROMPT = """\
You are an expert in manim Community Edition (manim>=0.18). Your job is to generate a complete, runnable Python script that produces a short narrative video for a given storyboard.

Strict requirements:
1. Output a SINGLE Python file as plain code. No markdown fences, no explanation, no comments before/after the code.
2. Only `from manim import *` is allowed for imports (plus standard library).
3. Define exactly one Scene subclass named `MainScene`.
4. For each storyboard item, animate a title (top) and content (below) using FadeIn / FadeOut transitions; show each scene 6-10 seconds.
5. Resolution 16:9. Total duration 60-150 seconds.
6. Use `Text(...)` for text. For Chinese support, prefer `Text(content, font="Microsoft YaHei")` and gracefully fallback to default font when not available — wrap font usage in a small try/except so the script never crashes due to missing fonts.
7. No external assets (no images, no audio, no external fonts files).
8. The script must run with `manim render -qm <file> MainScene` without manual edits.
"""

USER_PROMPT_TEMPLATE = """\
Topic: {topic}

Storyboard ({n} scenes):
{scenes_block}

Now produce the manim script for `MainScene`. Return ONLY the Python source code.
"""


def _build_prompt(topic: str, scenes: list[dict[str, Any]]) -> tuple[str, str]:
    lines: list[str] = []
    for i, s in enumerate(scenes, start=1):
        title = (s.get("title") or "").strip()
        content = (s.get("content") or "").strip().replace("\n", " ")
        lines.append(f"{i}. {title} — {content}")
    return SYSTEM_PROMPT, USER_PROMPT_TEMPLATE.format(
        topic=topic, n=len(scenes), scenes_block="\n".join(lines)
    )


_CODE_FENCE_RE = re.compile(r"^```[a-zA-Z]*\s*\n?|\n?```\s*$")


def _strip_code_fences(text: str) -> str:
    """去掉 LLM 可能加在外层的 ```python ... ``` 代码围栏。"""
    text = text.strip()
    if text.startswith("```"):
        # 去开头围栏
        text = re.sub(r"^```[a-zA-Z]*\s*\n", "", text)
    if text.endswith("```"):
        text = re.sub(r"\n?```\s*$", "", text)
    return text.strip()


# ---------- DB 进度更新 ----------


async def _update_task(
    task_id: str,
    *,
    stage: str | None = None,
    error: str | None = None,
    video_id: str | None = None,
    finished: bool = False,
) -> None:
    """开新会话写 task 状态。后台 task 与 HTTP request 的 session 不共用。"""
    async with SessionLocal() as db:
        stmt = select(VideoTaskORM).where(VideoTaskORM.id == task_id)
        orm = (await db.execute(stmt)).scalar_one_or_none()
        if orm is None:
            logger.warning("update_task: task %s not found", task_id)
            return
        if stage is not None:
            orm.stage = stage
        if error is not None:
            orm.error = error
        if video_id is not None:
            orm.video_id = video_id
        if finished:
            orm.finished_at = datetime.now(tz=timezone.utc)
        await db.commit()


async def _update_project_after_done(
    project_id: str, *, status: str, video_id: str | None = None, task_id: str | None = None
) -> None:
    async with SessionLocal() as db:
        stmt = select(ProjectORM).where(ProjectORM.id == project_id)
        orm = (await db.execute(stmt)).scalar_one_or_none()
        if orm is None:
            return
        orm.status = status
        if video_id is not None:
            orm.video_id = video_id
        if task_id is not None:
            orm.task_id = task_id
        await db.commit()


# ---------- 数据准备 ----------


async def _load_project_with_scenes(project_id: str) -> tuple[str, list[dict[str, Any]]]:
    async with SessionLocal() as db:
        stmt = select(ProjectORM).where(ProjectORM.id == project_id)
        proj = (await db.execute(stmt)).scalar_one_or_none()
        if proj is None:
            raise ValueError(f"project {project_id} not found")
        topic = proj.topic
        scene_stmt = (
            select(SceneORM)
            .where(SceneORM.project_id == project_id)
            .order_by(SceneORM.index)
        )
        scenes_orm = (await db.execute(scene_stmt)).scalars().all()
        scenes = [
            {"title": s.title, "content": s.content, "note": s.note}
            for s in scenes_orm
        ]
        if not scenes:
            # 用 topic 兜底成单场景，避免管线直接挂
            scenes = [
                {
                    "title": topic[:24],
                    "content": f"围绕主题《{topic}》的概览动画。",
                }
            ]
        return topic, scenes


# ---------- 阶段 1：LLM 生成脚本 ----------


async def _generate_manim_script(topic: str, scenes: list[dict[str, Any]]) -> str:
    """调 AIGCDESK 生成 manim Python 源码。"""
    system_prompt, user_prompt = _build_prompt(topic, scenes)
    # AIGCDESK payload 极简策略：build 阶段只会保留 model + messages，
    # 这里不再传 temperature / max_tokens / stream 等任何采样/控制参数。
    # system_prompt 会被 build 自动内联到首条 user 消息前。
    req = AIGCDeskChatRequest(
        messages=[
            ChatMessage(role="system", content=system_prompt),
            ChatMessage(role="user", content=user_prompt),
        ],
    )
    try:
        resp = await aigcdesk_service.aigcdesk_chat(req)
    except AIGCDeskAPIError as exc:
        raise RuntimeError(
            f"AIGCDESK 调用失败 status={exc.status_code}: {exc.body[:300]}"
        ) from exc

    code = str(resp.get("output_text") or "").strip()
    if not code:
        raise RuntimeError("AIGCDESK 返回空内容，无法生成 manim 脚本")
    code = _strip_code_fences(code)
    if "class MainScene" not in code:
        raise RuntimeError("LLM 输出不包含 MainScene，疑似生成失败")
    return code


# ---------- 阶段 2：跑 manim ----------


async def _run_manim(script_path: Path, work_dir: Path) -> Path:
    """跑 manim render 子进程，返回生成的 mp4 路径。"""
    media_dir = work_dir / "manim_out"
    media_dir.mkdir(parents=True, exist_ok=True)

    cmd = [
        sys.executable,
        "-m",
        "manim",
        "render",
        DEFAULT_QUALITY_FLAG,
        "--disable_caching",
        "--media_dir",
        str(media_dir),
        str(script_path),
        SCENE_CLASS_NAME,
    ]
    logger.info("manim cmd: %s", " ".join(cmd))

    proc = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
        cwd=str(work_dir),
    )
    try:
        stdout_b, stderr_b = await asyncio.wait_for(
            proc.communicate(), timeout=MANIM_TIMEOUT_SECONDS
        )
    except asyncio.TimeoutError as exc:
        proc.kill()
        await proc.wait()
        raise RuntimeError(
            f"manim 渲染超时（>{MANIM_TIMEOUT_SECONDS}s），已强制终止"
        ) from exc

    stdout = stdout_b.decode("utf-8", errors="replace")
    stderr = stderr_b.decode("utf-8", errors="replace")
    logger.info("manim stdout(tail):\n%s", stdout[-800:])

    if proc.returncode != 0:
        raise RuntimeError(
            f"manim 退出码 {proc.returncode}\nstderr(tail):\n{stderr[-1500:]}"
        )

    # 默认输出位置：{media_dir}/videos/{stem}/{quality_dir}/MainScene.mp4
    expected = media_dir / "videos" / script_path.stem / DEFAULT_QUALITY_DIR / f"{SCENE_CLASS_NAME}.mp4"
    if expected.is_file():
        return expected

    # 兜底：扫描整个 media_dir 找最新的 mp4
    candidates = sorted(media_dir.rglob("*.mp4"), key=lambda p: p.stat().st_mtime)
    if not candidates:
        raise RuntimeError("manim 退出码 0，但未在输出目录找到 mp4 文件")
    return candidates[-1]


# ---------- 阶段 3：抽缩略图（ffmpeg） ----------


async def _extract_thumbnail(video_path: Path, target: Path) -> bool:
    """用 ffmpeg 抽第 1 秒一帧做封面。返回是否成功。"""
    if shutil.which("ffmpeg") is None:
        logger.warning("ffmpeg not found, skip thumbnail")
        return False
    cmd = [
        "ffmpeg",
        "-y",
        "-ss",
        "1",
        "-i",
        str(video_path),
        "-vframes",
        "1",
        "-q:v",
        "3",
        str(target),
    ]
    proc = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.DEVNULL,
        stderr=asyncio.subprocess.PIPE,
    )
    try:
        _, err = await asyncio.wait_for(proc.communicate(), timeout=30)
    except asyncio.TimeoutError:
        proc.kill()
        await proc.wait()
        return False
    if proc.returncode != 0:
        logger.warning(
            "ffmpeg thumbnail failed rc=%s err=%s",
            proc.returncode,
            err.decode("utf-8", errors="replace")[-300:],
        )
        return False
    return True


def _probe_duration(video_path: Path) -> float:
    """轻量探测视频时长（秒），失败返回 0.0。"""
    if shutil.which("ffprobe") is None:
        return 0.0
    try:
        out = subprocess.check_output(
            [
                "ffprobe",
                "-v",
                "error",
                "-show_entries",
                "format=duration",
                "-of",
                "default=noprint_wrappers=1:nokey=1",
                str(video_path),
            ],
            timeout=10,
            text=True,
        ).strip()
        return float(out) if out else 0.0
    except (subprocess.SubprocessError, ValueError):
        return 0.0


# ---------- 主管线 ----------


async def run_pipeline(task_id: str, project_id: str, video_id: str) -> None:
    """异步主流程。捕获所有异常，确保 task 最终态写入 done 或 failed。"""
    media_root = Path(settings.MEDIA_ROOT).resolve()
    script_path = media_root / "scripts" / f"{video_id}.py"
    final_video_path = media_root / "videos" / f"{video_id}.mp4"
    final_thumb_path = media_root / "thumbnails" / f"{video_id}.jpg"

    work_dir: Path | None = None
    try:
        # ---------- 阶段 1：voice = LLM 生成脚本 ----------
        await _update_task(task_id, stage="voice")
        topic, scenes = await _load_project_with_scenes(project_id)
        code = await _generate_manim_script(topic, scenes)
        script_path.parent.mkdir(parents=True, exist_ok=True)
        script_path.write_text(code, encoding="utf-8")

        # ---------- 阶段 2：animation = 跑 manim ----------
        await _update_task(task_id, stage="animation")
        work_dir = Path(tempfile.mkdtemp(prefix=f"manim_{video_id}_"))
        produced = await _run_manim(script_path, work_dir)

        # ---------- 阶段 3：compose = 移动 + 抽缩略图 + 写 video_details ----------
        await _update_task(task_id, stage="compose")
        final_video_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(produced, final_video_path)
        final_thumb_path.parent.mkdir(parents=True, exist_ok=True)
        await _extract_thumbnail(final_video_path, final_thumb_path)

        duration = _probe_duration(final_video_path) or 60.0
        file_size = final_video_path.stat().st_size

        media_url = settings.MEDIA_BASE_URL.rstrip("/")
        async with SessionLocal() as db:
            db.add(
                VideoDetailORM(
                    id=video_id,
                    project_id=project_id,
                    task_id=task_id,
                    url=f"{media_url}/videos/{video_id}.mp4",
                    thumbnail_url=(
                        f"{media_url}/thumbnails/{video_id}.jpg"
                        if final_thumb_path.is_file()
                        else ""
                    ),
                    duration=duration,
                    resolution="720p",
                    ratio="16:9",
                    file_size=file_size,
                    created_at=datetime.now(tz=timezone.utc),
                )
            )
            await db.commit()

        # ---------- 完成 ----------
        await _update_task(
            task_id,
            stage="done",
            video_id=video_id,
            finished=True,
        )
        await _update_project_after_done(
            project_id, status="completed", video_id=video_id, task_id=task_id
        )
        logger.info("video pipeline done: task=%s video=%s", task_id, video_id)

    except Exception as exc:  # noqa: BLE001
        logger.exception("video pipeline failed: task=%s", task_id)
        await _update_task(
            task_id,
            stage="failed",
            error=str(exc)[:1000],
            finished=True,
        )
        await _update_project_after_done(project_id, status="failed", task_id=task_id)

    finally:
        if work_dir is not None and work_dir.exists():
            shutil.rmtree(work_dir, ignore_errors=True)


# ---------- 后台 task 持有引用，避免被 GC ----------

_BG_TASKS: set[asyncio.Task[Any]] = set()


def schedule_pipeline(task_id: str, project_id: str, video_id: str) -> None:
    """fire-and-forget 启动后台流水线。"""
    bg = asyncio.create_task(run_pipeline(task_id, project_id, video_id))
    _BG_TASKS.add(bg)
    bg.add_done_callback(_BG_TASKS.discard)
