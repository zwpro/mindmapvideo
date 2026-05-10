/**
 * Video / Task 业务接口。
 */

import { http } from './client'
import type { VideoDetail, VideoTask } from '@/types'

export const videoApi = {
  /** 创建任务（POST /videos/tasks），mock 实现下会立即返回 done 态任务 */
  createTask: (projectId: string) =>
    http.post<VideoTask>('/videos/tasks', { projectId }),

  /** 查询任务状态 */
  getTask: (taskId: string) => http.get<VideoTask>(`/videos/tasks/${taskId}`),

  /** 获取视频详情 */
  getDetail: (videoId: string) => http.get<VideoDetail>(`/videos/${videoId}`),
}
