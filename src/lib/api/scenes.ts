/**
 * Scenes / Outline 业务接口。
 *
 * 当前后端仅提供「按 topic 一次性生成完整分镜」一个端点：
 *   GET /api/v1/scenes?topic=xxx  →  Scene[]
 *
 * 大纲展开、保存等高级能力暂未在后端开放，前端如需持久化分镜，
 * 直接通过 projectApi.update(id, { scenes }) 写回项目即可。
 */

import { http } from './client'
import type { Scene } from '@/types'

export const sceneApi = {
  /** 一次性按 topic 拿全部分镜 */
  generateScenes: (topic: string) =>
    http.get<Scene[]>('/scenes', { query: { topic } }),
}
