import { defineStore } from 'pinia'
import type { GenerationStage, VideoDetail, VideoTask } from '@/types'
import { videoApi } from '@/lib/api'

interface State {
  tasks: Record<string, VideoTask>
  videos: Record<string, VideoDetail>
  loadingTask: Record<string, boolean>
  loadingVideo: Record<string, boolean>
  error: string | null
}

export const useTaskStore = defineStore('tasks', {
  state: (): State => ({
    tasks: {},
    videos: {},
    loadingTask: {},
    loadingVideo: {},
    error: null,
  }),
  getters: {
    taskById: (s) => (id: string) => s.tasks[id] || null,
    videoById: (s) => (id: string) => s.videos[id] || null,
  },
  actions: {
    upsert(task: VideoTask) {
      this.tasks[task.id] = { ...task }
    },
    setStage(id: string, stage: GenerationStage) {
      const task = this.tasks[id]
      if (!task) return
      task.stage = stage
      if (stage === 'done' || stage === 'failed') {
        task.finishedAt = new Date().toISOString()
      }
    },
    addVideo(detail: VideoDetail) {
      this.videos[detail.id] = detail
    },
    async fetchTask(taskId: string): Promise<VideoTask> {
      this.loadingTask[taskId] = true
      this.error = null
      try {
        const task = await videoApi.getTask(taskId)
        this.upsert(task)
        return task
      } catch (err) {
        this.error = err instanceof Error ? err.message : '获取任务失败'
        throw err
      } finally {
        this.loadingTask[taskId] = false
      }
    },
    async fetchVideo(videoId: string): Promise<VideoDetail> {
      this.loadingVideo[videoId] = true
      this.error = null
      try {
        const detail = await videoApi.getDetail(videoId)
        this.addVideo(detail)
        return detail
      } catch (err) {
        this.error = err instanceof Error ? err.message : '获取视频失败'
        throw err
      } finally {
        this.loadingVideo[videoId] = false
      }
    },
    async createTask(projectId: string): Promise<VideoTask> {
      this.error = null
      const task = await videoApi.createTask(projectId)
      this.upsert(task)
      return task
    },
  },
})
