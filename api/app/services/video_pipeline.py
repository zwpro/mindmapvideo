"""视频合成流水线：调 AIGCDESK 生成 manim 脚本 → 落盘 → manim 渲染 → 写库。

阶段映射（沿用 schemas.common.GenerationStage 字面量，不破坏前端契约）：
    voice     → 调 LLM 生成 manim 脚本
    animation → 跑 manim 子进程渲染
    compose   → 移动产物、抽缩略图、写 video_details
    done      → 全流程完成
    failed    → 任意阶段抛错，error 字段记录原因

调度模型（v2）：
    HTTP create_task 处理函数立即写一条 stage=voice 的 task 入库后返回，
    随后通过 `schedule_pipeline()` 用 `subprocess.Popen` detached 启动一个
    **独立 Python 进程**（入口：`app.scripts.run_video_pipeline`）来跑
    `run_pipeline()`。

为什么不再用 `asyncio.create_task` 挂在 uvicorn worker 内：
    开发模式下 `uvicorn --reload` 监听 .py 文件变更会斩 worker，原本挂在
    worker 内的协程一起死，task 永远卡在 animation 阶段，最终被
    startup cleanup hook 标 failed —— 这就是「animation 过长被自动收尾」
    的根因。detach 到独立进程后，worker 重启与 pipeline 进程互不影响。
"""

from __future__ import annotations

import asyncio
import logging
import os
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
from app.services import aigcdesk_service, socheap_service
from app.services.aigcdesk_service import AIGCDeskAPIError
from app.services.socheap_service import SoCheapAPIError

logger = logging.getLogger(__name__)

MANIM_TIMEOUT_SECONDS = 300  # manim 渲染超时上限
SCENE_CLASS_NAME = "MainScene"
DEFAULT_QUALITY_FLAG = "-qm"  # 720p30
DEFAULT_QUALITY_DIR = "720p30"

# BGM 资源约定：{MEDIA_ROOT}/bgm/{bgm_id}.{ext}，ext 命中下表第一个存在的文件
BGM_DIR_NAME = "bgm"
BGM_FILE_EXTS = (".mp3", ".m4a", ".aac", ".wav", ".ogg", ".flac")
BGM_MUX_TIMEOUT_SECONDS = 120
# 前端用 'bgm-none' 表示「不要 BGM」，且 setBgm 会把 config.bgm 直接置 None，
# 但保留这个 sentinel 是为了兜底旧数据/手改 DB 的情况。
BGM_NONE_ID = "bgm-none"

# 字体资源约定：把任意 .ttf/.otf/.ttc 丢到 {MEDIA_ROOT}/fonts/ 下，
# pipeline 会在每个 LLM 生成的 manim 脚本顶部自动注入 prelude：
#   1) manimpango.register_font(...) 注册全部字体；
#   2) 选一个 CJK family 作为 CJK_FONT；
#   3) 猴补 Text/MarkupText.__init__ 强制使用 CJK_FONT。
# Linux/Debian 没装中文字体时，这是不动系统就能解决中文乱码的最干净方案。
FONTS_DIR_NAME = "fonts"
FONT_FILE_EXTS = (".ttf", ".otf", ".ttc")


def _child_env() -> dict[str, str]:
    """子进程环境变量。

    Windows 下 capture_output=True 会把子进程 stdout/stderr 接到管道，
    click(_winconsole) 探测到非真终端时初始化会直接 0xC000041A 崩，
    塞这三个变量强制走 utf-8 + 旧式 stdio，绕开 _winconsole 路径。
    """
    env = os.environ.copy()
    env.setdefault("PYTHONIOENCODING", "utf-8")
    env.setdefault("PYTHONUTF8", "1")
    env.setdefault("PYTHONLEGACYWINDOWSSTDIO", "1")
    return env


# Windows 下不让子进程弹出控制台窗口；非 Windows 平台为 0（无副作用）
_CREATIONFLAGS = (
    subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0  # type: ignore[attr-defined]
)


# ---------- LLM Prompt ----------

SYSTEM_PROMPT = """\
你是 manim Community Edition专家。你的任务是把给定的分镜大纲生成一份完整、可直接运行的 Python 脚本，做成**思维导图 / 流程图**风格的动画。

严格要求：
1. 输出**单一** Python 文件源码，纯文本。**文件第 1 行必须是 `from manim import *`**（或其它合法的 `import` 语句）。
   - 不要加 markdown 围栏（` ```python `）。
   - 不要在代码前后写任何说明、分析、大纲、Step 1/Step 2、bullet/numbered list 等纯文本。
   - 不要把分镜内容以中文形式直接写在模块顶层当文档说明，那样会变成裸的中文字符让 Python 解析失败。
   - 反例（**严禁出现这种开头**）：
       1. Topic introduction
       2. Origin of concepts - Show sources from 《老子》and《周易》
       ```python
       from manim import *
   - 正例（必须直接这样开头）：
       from manim import *
       import math  # 可选
2. 只允许 `from manim import *` 这一个 import（如果确实需要，可以再加标准库 `math`）。
4. 视频总时长整体控制在 30~180 秒之间。
5. 文字一律用 `Text(...)`，**不要传 `font=` 参数**——项目会在脚本顶部自动注入 CJK 字体引导代码（注册项目自带字体并猴补 `Text.__init__`），你显式传的字体名会被覆盖。直接 `Text("中文内容")` 即可。**严禁**使用 `Tex` / `MathTex`（环境里没有 LaTeX）。
6. 不依赖任何外部资源（图片、音频、外部字体文件等）。背景色建议设为 `self.camera.background_color = "#0F172A"`（深石板蓝，与彩色节点搭配好看）。
7. 脚本必须能直接被 `manim render -qm <file> MainScene` 跑通，不需要任何手工修改；不要使用 `self.camera.frame` 等任何 OpenGL 专属特性，我们用默认 cairo 后端渲染。
8. **字符串字面量必须是合法 Python**。双引号字符串内部的 `"` 必须转义成 `\\"`，或者整段改用单引号；**严禁**写出 `"foo "bar" baz"` 这种裸嵌套引号。多行内容优先用三引号 `\"\"\"...\"\"\"`。最终脚本必须能通过 `compile()`，**绝不能**出现 SyntaxError。
"""

USER_PROMPT_TEMPLATE = """\
主题：{topic}

分镜（共 {n} 条）。每条中 "title" 是简短标签，"context" 是描述该分镜内容的文字，每个分镜是一个独立的动画场景，场景里的内容可根据 context 进一步展开，形式动画各不相同，好看。

{scenes_block}

请为 `MainScene` 生成思维导图风格的 manim 脚本：
"""


def _build_prompt(topic: str, scenes: list[dict[str, Any]]) -> tuple[str, str]:
    lines: list[str] = []
    for i, s in enumerate(scenes, start=1):
        title = (s.get("title") or "").strip()
        ctx = (s.get("content") or "").strip().replace("\n", " ")
        # 节点上不会显示 ctx 全文，仅供模型做"再压缩"参考
        lines.append(f"{i}. title=「{title}」  context=「{ctx}」")
    return SYSTEM_PROMPT, USER_PROMPT_TEMPLATE.format(
        topic=topic, n=len(scenes), scenes_block="\n".join(lines)
    )


_CODE_FENCE_RE = re.compile(r"^```[a-zA-Z]*\s*\n?|\n?```\s*$")
# 匹配第一个 ```python / ```py / ``` 代码围栏内的内容（DOTALL 让 . 吃换行）
_FENCED_BLOCK_RE = re.compile(
    r"```(?:python|py)?[ \t]*\r?\n(.*?)\r?\n[ \t]*```",
    re.DOTALL | re.IGNORECASE,
)
# 兜底：从第一个 import / from xxx import 行起截断，丢掉 LLM 写在前面的说明性文字
_FIRST_IMPORT_RE = re.compile(
    r"^[ \t]*(?:from[ \t]+\w[\w.]*[ \t]+import|import[ \t]+\w)",
    re.MULTILINE,
)


def _build_font_prelude() -> str:
    """生成插到 LLM manim 脚本最前面的字体注入 prelude。

    设计要点：
    - 把 {MEDIA_ROOT}/fonts/ 下所有字体文件 register 进 Pango，避免依赖系统字体。
    - 通过 list_fonts() 差集准确识别本次新注册的 family（兼容用户随便起的字体名）；
      如果没新增（开发机上字体已系统装好），再用一份 CJK 候选清单兜底匹配。
    - 用 monkey-patch 强行覆盖 manim.Text / MarkupText 的 font 参数，保证就算 LLM
      在脚本里写死 "Microsoft YaHei" 也会被换成 CJK_FONT —— manim 找不到指定字体
      时是**静默**退到 DejaVu Sans，根本进不到 LLM 写的 try/except 分支。
    - 全部包在 try/except 里，最坏情况下 prelude 静默失败，不影响下游 LLM 代码运行。
    """
    fonts_dir = (Path(settings.MEDIA_ROOT).resolve() / FONTS_DIR_NAME)
    # 用 repr 把 Windows 反斜杠安全转义进字符串字面量
    fonts_dir_literal = repr(str(fonts_dir))
    font_exts_literal = repr(FONT_FILE_EXTS)
    return f"""\
# === auto-injected by video_pipeline: CJK font bootstrap ===
from pathlib import Path as _Path

CJK_FONT = ""
try:
    import manimpango as _manimpango
    _FONTS_DIR = _Path({fonts_dir_literal})
    _before = set(_manimpango.list_fonts())
    if _FONTS_DIR.is_dir():
        for _f in _FONTS_DIR.iterdir():
            if _f.is_file() and _f.suffix.lower() in {font_exts_literal}:
                try:
                    _manimpango.register_font(str(_f))
                except Exception:
                    pass
    _after = set(_manimpango.list_fonts())
    _new = sorted(_after - _before)
    if _new:
        CJK_FONT = _new[0]
    else:
        for _cand in (
            "Noto Sans CJK SC", "Noto Sans CJK", "Noto Serif CJK SC",
            "Source Han Sans SC", "Source Han Sans CN",
            "WenQuanYi Zen Hei", "WenQuanYi Micro Hei",
            "Microsoft YaHei", "SimHei", "SimSun",
            "PingFang SC", "Hiragino Sans GB",
        ):
            if _cand in _after:
                CJK_FONT = _cand
                break
except Exception:
    pass

if CJK_FONT:
    try:
        import manim as _manim
        _orig_text_init = _manim.Text.__init__
        def _patched_text_init(self, *args, **kwargs):
            kwargs["font"] = CJK_FONT
            return _orig_text_init(self, *args, **kwargs)
        _manim.Text.__init__ = _patched_text_init
        if hasattr(_manim, "MarkupText"):
            _orig_mt_init = _manim.MarkupText.__init__
            def _patched_mt_init(self, *args, **kwargs):
                kwargs["font"] = CJK_FONT
                return _orig_mt_init(self, *args, **kwargs)
            _manim.MarkupText.__init__ = _patched_mt_init
    except Exception:
        pass
# === end font bootstrap ===

"""


def _strip_code_fences(text: str) -> str:
    """尽力把 LLM 输出剥成纯 Python 源码。

    支持几种常见的脏输出：
      1) 整段被 ```python ... ``` 包住                       → 取 fence 内容
      2) 代码块前后还有说明 / markdown 大纲（claude 老毛病）  → 取第一段 fence
      3) 完全没 fence 但前面塞了几行解释                      → 从第一个 import 行起截断
      4) 干净的 Python                                       → 原样返回
    """
    text = text.strip()
    if not text:
        return text

    # Case 1+2: 优先抽 fenced block，能抽到就直接拿
    fence = _FENCED_BLOCK_RE.search(text)
    if fence:
        return fence.group(1).strip()

    # Case 3: 没有 fence，但开头那段不是 Python → 从第一个 import 行起截断
    if not text.startswith(("from ", "import ", "#", '"""', "'''")):
        m = _FIRST_IMPORT_RE.search(text)
        if m:
            return text[m.start():].strip()

    # Case 4: 已经像 Python 了，原样返回
    return text


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
    project_id: str,
    *,
    status: str,
    video_id: str | None = None,
    task_id: str | None = None,
    thumbnail_url: str | None = None,
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
        # 用 is not None 而不是真值判断，允许显式传空串清空缩略图
        if thumbnail_url is not None:
            orm.thumbnail_url = thumbnail_url
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
    """调 AIGCDESK 生成 manim Python 源码；失败时回退 SoCheap。

    回退语义：
    - 主路 AIGCDESK 抛任何异常（API error / 网络超时 / API_KEY 未配置 503 ...）都触发回退
    - 回退 SoCheap 也失败时把两条线的错误一起 raise，方便日志定位
    - 主路返回空 output_text 也判定为失败，走回退
    """
    system_prompt, user_prompt = _build_prompt(topic, scenes)
    # payload 极简策略：build 阶段只会保留 model + messages，
    # 这里不再传 temperature / max_tokens / stream 等任何采样/控制参数。
    # system_prompt 会被 build 自动内联到首条 user 消息前。
    req = AIGCDeskChatRequest(
        messages=[
            ChatMessage(role="system", content=system_prompt),
            ChatMessage(role="user", content=user_prompt),
        ],
    )

    # ---------- 主路：AIGCDESK ----------
    aigcdesk_error: str | None = None
    code = ""
    try:
        resp = await aigcdesk_service.aigcdesk_chat(req)
        code = str(resp.get("output_text") or "").strip()
        if not code:
            aigcdesk_error = "AIGCDESK 返回空内容"
    except AIGCDeskAPIError as exc:
        aigcdesk_error = f"status={exc.status_code} body={exc.body[:300]}"
    except Exception as exc:  # noqa: BLE001 — 任何异常都回退，包括 httpx 超时 / 503 等
        aigcdesk_error = f"{type(exc).__name__}: {exc}"

    # ---------- 回退路：SoCheap ----------
    if aigcdesk_error is not None:
        logger.warning("AIGCDESK 失败，回退到 SoCheap：%s", aigcdesk_error)
        try:
            resp = await socheap_service.socheap_chat(req)
        except SoCheapAPIError as exc:
            raise RuntimeError(
                f"AIGCDESK 与 SoCheap 双双失败。\n"
                f"  AIGCDESK: {aigcdesk_error}\n"
                f"  SoCheap : status={exc.status_code} body={exc.body[:300]}"
            ) from exc
        except Exception as exc:  # noqa: BLE001
            raise RuntimeError(
                f"AIGCDESK 与 SoCheap 双双失败。\n"
                f"  AIGCDESK: {aigcdesk_error}\n"
                f"  SoCheap : {type(exc).__name__}: {exc}"
            ) from exc
        code = str(resp.get("output_text") or "").strip()
        if not code:
            raise RuntimeError(
                f"AIGCDESK 与 SoCheap 都返回空内容。\n"
                f"  AIGCDESK: {aigcdesk_error}\n"
                f"  SoCheap : 返回空 content"
            )
    code = _strip_code_fences(code)
    if "class MainScene" not in code:
        raise RuntimeError("LLM 输出不包含 MainScene，疑似生成失败")

    # 语法预检：LLM 偶尔会写出嵌套未转义的引号 / 缺逗号等问题，
    # 让 manim 来报错位置太深、堆栈混乱，这里直接 compile 一次给出清晰错误。
    try:
        compile(code, "<llm_manim_script>", "exec")
    except SyntaxError as exc:
        raise RuntimeError(
            f"LLM 生成的 manim 脚本存在 Python 语法错误："
            f"line {exc.lineno} offset {exc.offset}: {exc.msg}\n"
            f"问题片段：{(exc.text or '').strip()[:200]}"
        ) from exc
    return code


# ---------- 阶段 2：跑 manim ----------


async def _run_manim(script_path: Path, work_dir: Path) -> Path:
    """跑 manim render 子进程，返回生成的 mp4 路径。

    Windows 下 uvicorn 默认使用 SelectorEventLoop，不支持
    asyncio.create_subprocess_exec（NotImplementedError）。改用
    asyncio.to_thread + subprocess.run，跨平台/跨 loop 都能用，
    timeout 由 subprocess 自己处理（TimeoutExpired 会自动 kill）。
    """
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

    # 关键：stdout/stderr **不能用 PIPE / capture_output=True**。
    # manim 进度条会高速喷海量 stdout，Windows 下 subprocess.run 的 drain 线程
    # 在子进程结束瞬间拿不到 EOF，整个 communicate() 永远卡住，stage 就停在
    # animation 不会推进。改成把所有输出重定向到 work_dir/manim.log，
    # 跑完之后自己读 tail 即可，无 PIPE 就无死锁。
    log_path = work_dir / "manim.log"

    def _run() -> int:
        with log_path.open("wb") as logf:
            return subprocess.run(  # noqa: S603 — 命令行由我们构造
                cmd,
                cwd=str(work_dir),
                stdout=logf,
                stderr=subprocess.STDOUT,
                stdin=subprocess.DEVNULL,
                timeout=MANIM_TIMEOUT_SECONDS,
                check=False,
                env=_child_env(),
                creationflags=_CREATIONFLAGS,
            ).returncode

    try:
        returncode = await asyncio.to_thread(_run)
    except subprocess.TimeoutExpired as exc:
        raise RuntimeError(
            f"manim 渲染超时（>{MANIM_TIMEOUT_SECONDS}s），已强制终止"
        ) from exc

    log_text = (
        log_path.read_text(encoding="utf-8", errors="replace")
        if log_path.is_file()
        else ""
    )
    logger.info("manim log(tail):\n%s", log_text[-800:])

    if returncode != 0:
        raise RuntimeError(
            f"manim 退出码 {returncode}\nlog(tail):\n{log_text[-1500:]}"
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
    """用 ffmpeg 抽第 1 秒一帧做封面。返回是否成功。

    与 _run_manim 一样走 asyncio.to_thread + subprocess.run，
    避免 Windows SelectorEventLoop 不支持子进程的问题。
    """
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

    # ffmpeg 输出量小，但出于一致性也走"重定向到文件"路径，永远避开 PIPE 死锁。
    log_path = target.with_suffix(".ffmpeg.log")

    def _run() -> int:
        with log_path.open("wb") as logf:
            return subprocess.run(  # noqa: S603
                cmd,
                stdout=logf,
                stderr=subprocess.STDOUT,
                stdin=subprocess.DEVNULL,
                timeout=30,
                check=False,
                creationflags=_CREATIONFLAGS,
            ).returncode

    try:
        returncode = await asyncio.to_thread(_run)
    except subprocess.TimeoutExpired:
        return False

    if returncode != 0:
        tail = (
            log_path.read_text(encoding="utf-8", errors="replace")[-300:]
            if log_path.is_file()
            else ""
        )
        logger.warning("ffmpeg thumbnail failed rc=%s tail=%s", returncode, tail)
        return False

    # 缩略图出来后日志没用，删掉避免污染 thumbnails 目录
    log_path.unlink(missing_ok=True)
    return True


# ---------- 阶段 3.5：BGM 混音（ffmpeg） ----------


def _resolve_bgm_path(bgm_id: str) -> Path | None:
    """按前端 BGM_OPTIONS.id 在 {MEDIA_ROOT}/bgm 下找对应资源。

    支持多种常见格式，命中第一个存在的文件即返回。
    找不到/目录不存在时返回 None，由调用方降级处理。
    """
    if not bgm_id or bgm_id == BGM_NONE_ID:
        return None
    bgm_dir = Path(settings.MEDIA_ROOT).resolve() / BGM_DIR_NAME
    if not bgm_dir.is_dir():
        return None
    for ext in BGM_FILE_EXTS:
        candidate = bgm_dir / f"{bgm_id}{ext}"
        if candidate.is_file():
            return candidate
    return None


async def _load_bgm_setting(project_id: str) -> tuple[Path | None, float]:
    """从 project.config 读 BGM 选择，返回 (bgm_path, volume)。

    任一缺失/非法/文件不存在都返回 (None, 1.0)，调用方据此降级为无 BGM。
    volume 兜底 1.0，并裁剪到 [0, 4]，避免 ffmpeg volume filter 收到怪值。
    """
    async with SessionLocal() as db:
        stmt = select(ProjectORM).where(ProjectORM.id == project_id)
        proj = (await db.execute(stmt)).scalar_one_or_none()
        if proj is None or not proj.config:
            return None, 1.0
        bgm_cfg = (proj.config or {}).get("bgm")
        if not isinstance(bgm_cfg, dict):
            return None, 1.0
        bgm_id = str(bgm_cfg.get("id") or "").strip()
        try:
            volume = float(bgm_cfg.get("volume", 1.0))
        except (TypeError, ValueError):
            volume = 1.0
        volume = max(0.0, min(volume, 4.0))
        return _resolve_bgm_path(bgm_id), volume


async def _mux_bgm(
    video_path: Path, bgm_path: Path, volume: float, output_path: Path
) -> bool:
    """用 ffmpeg 把 BGM 混进 manim 视频。

    - manim 输出没有音轨，所以直接把 BGM 当唯一音源
    - -stream_loop -1 让 BGM 短于视频时自动循环
    - -shortest 保证总长度等于视频长度
    - -c:v copy 不重新编码视频，速度只比 thumbnail 多几秒
    - 失败返回 False，调用方降级为 shutil.copy2 走无 BGM 路径
    """
    if shutil.which("ffmpeg") is None:
        logger.warning("ffmpeg not found, skip bgm mux")
        return False

    cmd = [
        "ffmpeg",
        "-y",
        "-i",
        str(video_path),
        "-stream_loop",
        "-1",
        "-i",
        str(bgm_path),
        "-filter:a",
        f"volume={volume:.3f}",
        "-map",
        "0:v:0",
        "-map",
        "1:a:0",
        "-c:v",
        "copy",
        "-c:a",
        "aac",
        "-b:a",
        "128k",
        "-shortest",
        str(output_path),
    ]

    # 与 _run_manim / _extract_thumbnail 同构：日志重定向到文件，永远绕开 PIPE。
    log_path = output_path.with_suffix(".bgm.log")

    def _run() -> int:
        with log_path.open("wb") as logf:
            return subprocess.run(  # noqa: S603
                cmd,
                stdout=logf,
                stderr=subprocess.STDOUT,
                stdin=subprocess.DEVNULL,
                timeout=BGM_MUX_TIMEOUT_SECONDS,
                check=False,
                creationflags=_CREATIONFLAGS,
            ).returncode

    try:
        returncode = await asyncio.to_thread(_run)
    except subprocess.TimeoutExpired:
        logger.warning("ffmpeg bgm mux timeout for %s", video_path.name)
        return False

    if returncode != 0:
        tail = (
            log_path.read_text(encoding="utf-8", errors="replace")[-400:]
            if log_path.is_file()
            else ""
        )
        logger.warning("ffmpeg bgm mux failed rc=%s tail=%s", returncode, tail)
        # 失败的半成品别留在 videos/ 下被外部当成最终产物
        output_path.unlink(missing_ok=True)
        return False

    log_path.unlink(missing_ok=True)
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
        # 在 LLM 代码前面拼一段 CJK 字体注入 prelude：
        # 保证 Linux/Debian 上不装系统字体也能正常渲染中文（用 api/media/fonts/ 下的字体包）。
        script_path.write_text(
            _build_font_prelude() + code, encoding="utf-8"
        )

        # ---------- 阶段 2：animation = 跑 manim ----------
        await _update_task(task_id, stage="animation")
        work_dir = Path(tempfile.mkdtemp(prefix=f"manim_{video_id}_"))
        produced = await _run_manim(script_path, work_dir)

        # ---------- 阶段 3：compose = 移动 + 混 BGM + 抽缩略图 + 写 video_details ----------
        await _update_task(task_id, stage="compose")
        final_video_path.parent.mkdir(parents=True, exist_ok=True)

        # 配了 BGM 就 ffmpeg 直接 mux 到 final_video_path；否则原样拷贝。
        # mux 失败一律降级为无 BGM，不能让 BGM 缺失把整条管线带挂。
        bgm_path, bgm_volume = await _load_bgm_setting(project_id)
        muxed = False
        if bgm_path is not None:
            muxed = await _mux_bgm(produced, bgm_path, bgm_volume, final_video_path)
            if not muxed:
                logger.warning(
                    "bgm mux failed, fallback to no-bgm for task=%s", task_id
                )
        if not muxed:
            shutil.copy2(produced, final_video_path)

        final_thumb_path.parent.mkdir(parents=True, exist_ok=True)
        await _extract_thumbnail(final_video_path, final_thumb_path)

        duration = _probe_duration(final_video_path) or 60.0
        file_size = final_video_path.stat().st_size

        media_url = settings.MEDIA_BASE_URL.rstrip("/")
        # 缩略图 URL 抽出来：video_details 和 projects 两表共用，
        # 避免两边算两次导致不一致（之前 project 表根本没写过这个字段）
        thumbnail_url = (
            f"{media_url}/thumbnails/{video_id}.jpg"
            if final_thumb_path.is_file()
            else ""
        )
        async with SessionLocal() as db:
            db.add(
                VideoDetailORM(
                    id=video_id,
                    project_id=project_id,
                    task_id=task_id,
                    url=f"{media_url}/videos/{video_id}.mp4",
                    thumbnail_url=thumbnail_url,
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
            project_id,
            status="completed",
            video_id=video_id,
            task_id=task_id,
            thumbnail_url=thumbnail_url,
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


# ---------- 调度入口：detached subprocess ----------


def _pipeline_log_path(task_id: str) -> Path:
    """每个 pipeline 子进程都写一份独立日志，便于排障。"""
    root = Path(settings.MEDIA_ROOT).resolve() / "pipeline_logs"
    root.mkdir(parents=True, exist_ok=True)
    return root / f"{task_id}.log"


# Windows 下的 detach 标志：CREATE_NEW_PROCESS_GROUP 让子进程脱离父进程的 Ctrl+C，
# DETACHED_PROCESS 让子进程不继承父进程控制台（也避免 click _winconsole 探测崩），
# CREATE_NO_WINDOW 不弹窗口。三个都加上才能真正与 uvicorn worker 解耦。
if sys.platform == "win32":
    _DETACH_CREATIONFLAGS = (
        subprocess.DETACHED_PROCESS  # type: ignore[attr-defined]
        | subprocess.CREATE_NEW_PROCESS_GROUP  # type: ignore[attr-defined]
        | subprocess.CREATE_NO_WINDOW  # type: ignore[attr-defined]
    )
else:
    _DETACH_CREATIONFLAGS = 0


def schedule_pipeline(task_id: str, project_id: str, video_id: str) -> None:
    """fire-and-forget 启动 detached pipeline 子进程。

    立刻返回（毫秒级），子进程独立于 uvicorn worker 生命周期，worker reload
    或崩溃都不会影响它。子进程内部自己写 DB，前端通过轮询 /api/v1/videos/tasks
    取最新状态即可。
    """
    log_path = _pipeline_log_path(task_id)
    # 子进程工作目录用 api/ 根（也就是 main.py 所在目录的父目录），
    # 让 settings 能正常加载 .env，并让 manim 工作目录与开发时一致。
    api_root = Path(__file__).resolve().parents[2]

    cmd = [
        sys.executable,
        "-m",
        "app.scripts.run_video_pipeline",
        task_id,
        project_id,
        video_id,
    ]

    # 父进程持有的 log 文件句柄只用于把 fd 传给子进程，Popen 返回后立刻关闭
    # 父端（子进程已经在 OS 层 dup 出自己的 fd，不受影响）。否则父进程会
    # 一直持有 append 模式的 fd，长期跑会泄漏。
    log_file = log_path.open("ab")
    try:
        popen_kwargs: dict[str, Any] = {
            "cwd": str(api_root),
            "env": _child_env(),
            "stdin": subprocess.DEVNULL,
            "stdout": log_file,
            "stderr": subprocess.STDOUT,
            "close_fds": True,
        }
        if sys.platform == "win32":
            popen_kwargs["creationflags"] = _DETACH_CREATIONFLAGS
        else:
            # POSIX：start_new_session=True 等价于 setsid，让子进程成为新会话组组长，
            # 父进程退出（uvicorn worker 死）不会带走它。
            popen_kwargs["start_new_session"] = True

        try:
            proc = subprocess.Popen(cmd, **popen_kwargs)  # noqa: S603 — 命令行由我们构造
        except Exception:
            logger.exception("schedule_pipeline: failed to spawn subprocess task=%s", task_id)
            # 启动失败也不能让 task 永远卡 voice：fallback 退到 inline 协程，
            # 由当前 worker 把它跑完（与旧行为一致）。
            bg = asyncio.create_task(run_pipeline(task_id, project_id, video_id))
            _BG_FALLBACK_TASKS.add(bg)
            bg.add_done_callback(_BG_FALLBACK_TASKS.discard)
            return
    finally:
        log_file.close()

    logger.info(
        "schedule_pipeline: spawned subprocess pid=%s task=%s log=%s",
        proc.pid,
        task_id,
        log_path,
    )


# fallback 协程引用池（detach 启动失败时才会用到，正常路径用不到）
_BG_FALLBACK_TASKS: set[asyncio.Task[Any]] = set()
