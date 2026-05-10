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

## 快速开始

只要本机有 **Python 3.11+** 即可，下面给三种方案任选一种。

### 方案 A：pip + venv（推荐，零额外依赖）

```bash
cd api

# 1. 创建虚拟环境（Python 自带 venv）
python -m venv .venv

# 2. 激活
.venv\Scripts\activate          # Windows PowerShell / CMD
# source .venv/bin/activate     # macOS / Linux / Git Bash

# 3. 升级 pip 并安装依赖
python -m pip install --upgrade pip
pip install -e ".[dev]"
# 或者用 requirements.txt 等价方式：
# pip install -r requirements.txt

# 4. 配置环境变量
copy .env.example .env          # Windows
# cp .env.example .env          # macOS/Linux

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
