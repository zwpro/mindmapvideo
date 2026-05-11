"""独立进程入口：跑一次视频合成 pipeline。

调用方式（HTTP create_task 后由 `video_pipeline.schedule_pipeline` 通过
`subprocess.Popen` detached 启动；用户也可以在终端直接调试）：

    python -m app.scripts.run_video_pipeline <task_id> <project_id> <video_id>

为什么要独立进程：uvicorn `--reload` 在开发模式下，任何 .py 文件保存都会斩
worker，原本挂在 worker 内的 `asyncio.create_task(run_pipeline)` 也会一起死，
然后服务重启时被 cleanup hook 标 failed —— 表现为「animation 阶段过长
然后被自动收尾」。把 pipeline detach 到独立进程后，worker 重启不再影响
pipeline 进程，它会自顾自跑完写库。
"""

from __future__ import annotations

import asyncio
import logging
import sys


def _setup_logging() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
    )


def main(argv: list[str] | None = None) -> int:
    _setup_logging()
    args = argv if argv is not None else sys.argv[1:]
    if len(args) != 3:
        sys.stderr.write(
            "usage: python -m app.scripts.run_video_pipeline <task_id> <project_id> <video_id>\n"
        )
        return 2
    task_id, project_id, video_id = args

    # 延迟导入：让 logging 配好后再 import，pipeline 内部 logger 才能正确生效
    from app.services.video_pipeline import run_pipeline

    logger = logging.getLogger("app.scripts.run_video_pipeline")
    logger.info(
        "pipeline subprocess start: task=%s project=%s video=%s",
        task_id,
        project_id,
        video_id,
    )
    try:
        asyncio.run(run_pipeline(task_id, project_id, video_id))
    except Exception:  # noqa: BLE001 — 顶层兜底，run_pipeline 内部已做 failed 标记
        logger.exception("pipeline subprocess crashed at top-level")
        return 1
    logger.info("pipeline subprocess done: task=%s", task_id)
    return 0


if __name__ == "__main__":
    sys.exit(main())
