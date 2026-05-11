# Mindmap API

Mindmap 视频生成平台后端，基于 **FastAPI + Pydantic v2 + SQLAlchemy 2.0**。

与同目录 `../src/`（Vue 3 前端）共用 `Project / Scene / VideoConfig` 模型。

## 目录结构

```
api/
├── app/
│   ├── main.py                 入口（FastAPI app + CORS + 路由挂载）
│   ├── core/
│   │   ├── config.py           Settings（读 .env）
│   │   └── security.py         JWT、密码哈希（占位）
│   ├── api/v1/
│   │   ├── router.py           v1 路由聚合
│   │   └── endpoints/
│   │       ├── projects.py     /api/v1/projects
│   │       ├── scenes.py       /api/v1/scenes
│   │       └── videos.py       /api/v1/videos
│   ├── schemas/                Pydantic 模型，对齐前端 types/index.ts
│   ├── services/               业务逻辑（替换前端 outlineMock / videoMock）
│   ├── db/                     SQLAlchemy 会话 / 基类（含 base.py 聚合 ORM）
│   └── workers/                Celery 长任务（视频合成）
├── alembic/                    数据库迁移
│   ├── env.py                  从 settings 读 DSN，兼容 async/sync 驱动
│   ├── script.py.mako          版本文件模板
│   └── versions/               生成的迁移脚本
├── alembic.ini
├── docker-compose.dev.yml      本地一键起 MySQL + Redis
├── tests/
├── pyproject.toml
└── .env.example
```

## 系统依赖（视频合成必装）

视频合成走 `manim` + `ffmpeg` 两个外部进程，Python 包靠 `pip` 能装上，但下面这几样得自己装好并保证在 `PATH` 里：

| 依赖 | 用途 | 是否必装 |
| --- | --- | --- |
| **ffmpeg** | manim 编码 mp4；`video_pipeline.py` 抽缩略图、混 BGM | ✅ 必装 |
| **Microsoft YaHei / Source Han Sans 等中文字体** | manim 渲染中文 `Text(...)` | ✅ 必装（Windows 自带 YaHei，Linux/macOS 需自行安装） |
| **Cairo / Pango + pkg-config**（Linux/macOS） | manim 默认 cairo 后端；pip 装 `pycairo` / `manimpango` 时要从源码编译 | ✅ Linux/macOS 必装；Windows 走 wheel 通常自带 |
| ~~LaTeX (MiKTeX / TeX Live)~~ | 本项目 prompt 里**严禁** `Tex` / `MathTex`，**不要装** | ❌ 不需要 |

### 安装 ffmpeg

```bash
# Windows（任选其一）
winget install Gyan.FFmpeg          # 官方推荐
# choco install ffmpeg              # 用 Chocolatey
# scoop install ffmpeg              # 用 Scoop

# macOS
brew install ffmpeg

# Ubuntu / Debian
sudo apt update && sudo apt install -y ffmpeg
```

装完后**新开一个终端**执行 `ffmpeg -version` 能打印版本号即可。

### 安装 Cairo / Pango / pkg-config（仅 Linux & macOS 需要）

Windows 装 `manim` 时 pip 会直接拉 `pycairo` / `manimpango` 的预编译 wheel，**可以跳过本节**。
Linux / macOS 上 `pycairo` 没有官方 wheel，pip 会去源码编译，必须先装好 `pkg-config` + cairo / pango 开发头文件：

```bash
# Ubuntu / Debian
sudo apt update
sudo apt install -y build-essential python3-dev pkg-config libcairo2-dev libpango1.0-dev

# Fedora / RHEL
sudo dnf install -y gcc python3-devel pkg-config cairo-devel pango-devel

# Arch
sudo pacman -S --needed base-devel python pkg-config cairo pango

# macOS
brew install pkg-config cairo pango
```

> 如果 `pip install -e ".[dev]"` 报 **`Did not find pkg-config` / `Run-time dependency cairo found: NO` / `metadata-generation-failed (pycairo)`**，就是这步没做。装完上面的包后**重开终端、重激活 venv**再 `pip install` 一次即可。

### 验证 manim 能跑

激活 venv 并 `pip install -e ".[dev]"` 之后：

```bash
python -m manim --version
```

打印出 `Manim Community v0.18.x` 即视为安装成功；实际渲染由后端通过 `python -m manim render -qm ...` 子进程触发，参数见 `app/services/video_pipeline.py:_run_manim`。

## 快速开始

只要本机有 **Python 3.11+** 即可，下面给三种方案任选一种。

### 方案 A：pip + venv（推荐，零额外依赖）

```bash
cd api

# 1. 创建虚拟环境（Python 自带 venv）
python -m venv .venv

# 2. 激活（按你的系统二选一，不要混抄！）
source .venv/bin/activate       # macOS / Linux / WSL / Git Bash
# .venv\Scripts\activate        # Windows PowerShell / CMD（注意是反斜杠 + Scripts，bash 下抄这行会把反斜杠吃掉）

# 3. 升级 pip 并安装依赖
python -m pip install --upgrade pip
pip install -e ".[dev]"

# 4. 配置环境变量（按你的系统二选一）
cp .env.example .env            # macOS / Linux / WSL
# copy .env.example .env        # Windows

# 5. 启动开发服务器
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 方案 B：uv（可选，安装速度快约 10 倍）

需要先装一次 uv：<https://docs.astral.sh/uv/getting-started/installation/>

```bash
cd api
uv venv
.venv\Scripts\activate
uv pip install -e ".[dev]"
copy .env.example .env
uvicorn app.main:app --reload --port 8000
```

### 方案 C：poetry（如果团队已经在用）

```bash
cd api
poetry install --with dev
poetry shell
uvicorn app.main:app --reload --port 8000
```

启动后访问：

- 接口：<http://localhost:8000/api/v1/...>
- Swagger UI：<http://localhost:8000/docs>
- OpenAPI JSON：<http://localhost:8000/openapi.json>

## 与前端联调

前端 `vite.config.ts` 已配置 `/api` 代理到 `http://localhost:8000`，前端只需 `fetch('/api/v1/...')` 即可。

## 自动同步前端 TS 类型

后端启动后，在前端目录运行：

```bash
npx openapi-typescript http://localhost:8000/openapi.json -o src/types/api.ts
```

即可把后端 schema 完整生成为 TS 类型。

## 常用命令

```bash
# 代码规范
ruff check .
ruff format .

# 类型检查
mypy app

# 单元测试
pytest
```

## 数据库迁移（Alembic）

DSN 由 `alembic/env.py` 自动从 `app.core.config.settings.DATABASE_URL` 读取，无需在 `alembic.ini` 里硬编码。
**开发与生产统一使用 MySQL**（异步驱动 `asyncmy`，Alembic 通过 `AsyncEngine + run_sync` 复用同一份 DSN），避免方言差异导致的环境不一致问题。

### 本地启动 MySQL

最省心的方式是用 Docker 起一个本地实例（已附 `docker-compose.dev.yml`）：

```bash
# 启动 MySQL 8（端口 3306，账号/密码/库名都是 mindmap）
docker compose -f docker-compose.dev.yml up -d mysql

# 停止
docker compose -f docker-compose.dev.yml down
```

如果本机已有 MySQL，手动建库即可：

```sql
CREATE DATABASE mindmap CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci;
CREATE USER 'mindmap'@'%' IDENTIFIED BY 'mindmap';
GRANT ALL PRIVILEGES ON mindmap.* TO 'mindmap'@'%';
FLUSH PRIVILEGES;
```

### 迁移命令

```bash
# 1. 新增 ORM 模型后，把它 import 到 app/db/base.py
#    （Alembic autogenerate 通过 Base.metadata 扫描）

# 2. 生成迁移脚本（自动 diff 模型与数据库）
alembic revision --autogenerate -m "init schema"

# 3. 应用到数据库
alembic upgrade head

# 4. 回滚一步 / 回滚到指定版本
alembic downgrade -1
alembic downgrade <revision>

# 5. 查看当前版本 / 历史
alembic current
alembic history

# 6. 离线生成 SQL（仅渲染，不连库）
alembic upgrade head --sql > migration.sql
```

> 第一条迁移生成后，可删除 `alembic/versions/.gitkeep`。

## 路线图

- [x] 项目骨架、分镜生成接口（mock 数据）
- [ ] 接入 OpenAI/Claude 真实 LLM
- [ ] MySQL + Alembic 迁移
- [ ] Celery + Redis 视频合成任务队列
- [ ] JWT 鉴权
- [ ] Docker Compose（前端 + 后端 + MySQL + Redis）
