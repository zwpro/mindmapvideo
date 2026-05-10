# Mindmap · 前端

基于 Vue 3 + TypeScript + Vite 的思维导图视频生成平台前端。后端在 `api/` 目录。

## 前端 · 环境变量与 API 域名

Vite 按 `mode` 自动加载对应 `.env` 文件：

| 文件 | 生效时机 | 是否进 git |
|---|---|---|
| `.env.example` | 仅作模板参考 | ✅ 进 git |
| `.env.development` | `npm run dev` | ✅ 进 git |
| `.env.production` | `npm run build` | ✅ 进 git |
| `.env.*.local` | 本机覆盖 | ❌ 已在 `.gitignore` |

关键变量：

```bash
VITE_API_BASE_URL=            # 后端域名；开发留空走 proxy，生产填 https://api.xxx.com
VITE_API_PREFIX=/api/v1       # 后端统一前缀
VITE_DEV_PROXY_TARGET=http://localhost:8000   # dev server 反向代理目标（仅 dev）
```

### 开发环境（推荐：走 Vite proxy）

`.env.development` 里 `VITE_API_BASE_URL` **留空**，前端请求走相对路径 `/api/v1/...`，由 `vite.config.ts` 里的 proxy 转发到 `VITE_DEV_PROXY_TARGET`（默认 `http://localhost:8000`）。

好处：浏览器不会发 CORS 预检，也不用在后端额外维护开发域名白名单。

```bash
# 1. 启后端（另开一个终端）
cd api
docker compose -f docker-compose.dev.yml up -d   # MySQL + Redis
uvicorn app.main:app --reload

# 2. 启前端
npm install
npm run dev    # 打开 http://localhost:5173
```

### 生产环境

`.env.production` 填真实的后端域名，构建时会被静态替换进 bundle：

```bash
VITE_API_BASE_URL=https://api.mindmap.example.com
```

然后：

```bash
npm run build       # 产物在 dist/
npm run preview     # 本机预览生产构建
```

> 注意：后端 FastAPI 的 `CORS_ORIGINS` 必须包含前端域名（例如 `https://mindmap.example.com`），否则浏览器会拦截。

### 个人本地覆盖

临时想连别的后端（如同事本机、远程测试环境），建 `.env.development.local`：

```bash
VITE_API_BASE_URL=http://192.168.1.20:8000
```

此文件不会进 git，只影响你本机。

## 前端代码结构

```
src/
  lib/api/          # 统一 HTTP 客户端与业务接口
    config.ts       # 读取 VITE_* 环境变量，暴露 API_BASE/API_PREFIX
    client.ts       # fetch 封装 + ApiError + 超时 + token 注入
    projects.ts     # 项目接口
    scenes.ts       # 大纲 / 分镜接口
    videos.ts       # 视频任务接口
    index.ts        # 桶文件，统一 import
  pages/            # 路由页
  components/       # 展示 / 业务组件
  stores/           # Pinia
  composables/      # 组合式函数
  types/            # 全局类型
```

## 常用脚本

```bash
npm run dev       # 本地开发
npm run build     # 生产构建（含 vue-tsc 类型检查）
npm run preview   # 预览生产构建
npm run check     # 仅跑类型检查
npm run lint      # ESLint
```

## 使用示例

```ts
// 任何组件或 store 里
import { projectApi, ApiError } from '@/lib/api'

try {
  const projects = await projectApi.list()
  console.log(projects)
} catch (err) {
  if (err instanceof ApiError && err.status === 401) {
    // 未登录
  } else {
    console.error(err)
  }
}
```

---

## 原始模板信息

This template should help get you started developing with Vue 3 and TypeScript in Vite. The template uses Vue 3 `<script setup>` SFCs, check out the [script setup docs](https://v3.vuejs.org/api/sfc-script-setup.html#sfc-script-setup) to learn more.

Learn more about the recommended Project Setup and IDE Support in the [Vue Docs TypeScript Guide](https://vuejs.org/guide/typescript/overview.html#project-setup).
