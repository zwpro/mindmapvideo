/**
 * 统一的 API 入口桶。
 *
 * 用法：
 *   import { projectApi, sceneApi, videoApi, userApi } from '@/lib/api'
 */

export * from './config'
export * from './client'
export { projectApi } from './projects'
export type { CreateProjectPayload } from './projects'
export { sceneApi } from './scenes'
export { videoApi } from './videos'
export { userApi } from './users'
export type { UpdateUserPayload, CreateNotificationPayload } from './users'
