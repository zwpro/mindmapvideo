/**
 * Projects 业务接口。
 *
 * 组件侧使用示例：
 *   import { projectApi } from '@/lib/api'
 *   const list = await projectApi.list()
 */

import { http } from './client'
import type { Project, VideoConfig } from '@/types'

export interface CreateProjectPayload {
  topic: string
  config?: Partial<VideoConfig>
}

export const projectApi = {
  list: () => http.get<Project[]>('/projects'),

  get: (id: string) => http.get<Project>(`/projects/${id}`),

  create: (payload: CreateProjectPayload) => http.post<Project>('/projects', payload),

  update: (id: string, payload: Partial<Project>) =>
    http.patch<Project>(`/projects/${id}`, payload),

  delete: (id: string) => http.delete<void>(`/projects/${id}`),
}
