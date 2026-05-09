import { defineStore } from 'pinia'
import type { GenerationStage, VideoDetail, VideoTask } from '@/types'

interface State {
  tasks: Record<string, VideoTask>
  videos: Record<string, VideoDetail>
}

export const useTaskStore = defineStore('tasks', {
  state: (): State => ({
    tasks: {},
    videos: {
      'video-demo-1': {
        id: 'video-demo-1',
        projectId: 'proj-demo-1',
        taskId: 'task-demo-1',
        url: 'https://www.w3schools.com/html/mov_bbb.mp4',
        thumbnailUrl:
          'https://trae-api-cn.mchost.guru/api/ide/v1/text_to_image?prompt=cinematic%20mindmap%20video%20thumbnail%2C%20deep%20navy%20background%2C%20cyan%20neon%20mindmap%20nodes%2C%20premium%20look&image_size=landscape_16_9',
        duration: 184,
        resolution: '1080p',
        ratio: '16:9',
        fileSize: 28_600_000,
        createdAt: new Date(Date.now() - 86_400_000).toISOString(),
      },
    },
  }),
  getters: {
    taskById: (s) => (id: string) => s.tasks[id] || null,
    videoById: (s) => (id: string) => s.videos[id] || null,
  },
  actions: {
    upsert(task: VideoTask) {
      this.tasks[task.id] = { ...task }
    },
    setProgress(id: string, stage: GenerationStage, progress: number) {
      const task = this.tasks[id]
      if (!task) return
      task.stage = stage
      task.progress = progress
      if (stage === 'done' || stage === 'failed') {
        task.finishedAt = new Date().toISOString()
      }
    },
    addVideo(detail: VideoDetail) {
      this.videos[detail.id] = detail
    },
  },
  persist: {
    key: 'mindmap.tasks',
  },
})
