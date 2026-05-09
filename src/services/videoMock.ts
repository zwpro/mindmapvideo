import { nanoid } from 'nanoid'
import type {
  GenerationStage,
  Project,
  VideoConfig,
  VideoDetail,
  VideoTask,
} from '@/types'

export interface ProgressEvent {
  stage: GenerationStage
  progress: number
  remainingSeconds?: number
  message?: string
}

export interface VideoGenerationHandle {
  taskId: string
  cancel(): void
}

const STAGES: GenerationStage[] = ['voice', 'animation', 'compose', 'done']

interface StartParams {
  project: Project
  onEvent: (event: ProgressEvent) => void
  onTaskCreated?: (task: VideoTask) => void
  onComplete?: (video: VideoDetail) => void
}

export function startVideoGeneration({
  project,
  onEvent,
  onTaskCreated,
  onComplete,
}: StartParams): VideoGenerationHandle {
  const taskId = `task-${nanoid(8)}`
  const startedAt = new Date().toISOString()
  const task: VideoTask = {
    id: taskId,
    projectId: project.id,
    stage: 'voice',
    progress: 0,
    startedAt,
  }
  onTaskCreated?.(task)

  let cancelled = false
  let stageIndex = 0
  let progress = 0
  const totalSeconds = estimateSeconds(project.config)

  const tick = () => {
    if (cancelled) return
    progress += 4 + Math.random() * 6
    if (progress >= 100) {
      progress = 100
      const stage = STAGES[stageIndex]
      onEvent({
        stage,
        progress: 100,
        remainingSeconds: Math.max(
          0,
          Math.round(totalSeconds * (1 - (stageIndex + 1) / STAGES.length)),
        ),
        message: stageMessage(stage, true),
      })
      stageIndex += 1
      progress = 0
      if (stageIndex >= STAGES.length - 1) {
        const videoId = `video-${nanoid(8)}`
        const video: VideoDetail = {
          id: videoId,
          projectId: project.id,
          taskId,
          url: 'https://www.w3schools.com/html/mov_bbb.mp4',
          thumbnailUrl: project.thumbnailUrl,
          duration: totalSeconds,
          resolution: project.config.resolution,
          ratio: project.config.ratio,
          fileSize: estimateFileSize(project.config, totalSeconds),
          createdAt: new Date().toISOString(),
        }
        onEvent({ stage: 'done', progress: 100, remainingSeconds: 0 })
        onComplete?.(video)
        return
      }
    }
    const stage = STAGES[stageIndex]
    const overall = (stageIndex + progress / 100) / (STAGES.length - 1)
    const remaining = Math.max(1, Math.round(totalSeconds * (1 - overall)))
    onEvent({
      stage,
      progress: Math.min(100, Math.round(progress)),
      remainingSeconds: remaining,
      message: stageMessage(stage),
    })
    setTimeout(tick, 220 + Math.random() * 220)
  }

  setTimeout(tick, 280)

  return {
    taskId,
    cancel() {
      cancelled = true
    },
  }
}

function stageMessage(stage: GenerationStage, finished = false): string {
  if (finished) {
    switch (stage) {
      case 'voice':
        return '配音合成完成'
      case 'animation':
        return '动画渲染完成'
      case 'compose':
        return '视频合成完成'
      default:
        return ''
    }
  }
  switch (stage) {
    case 'voice':
      return '正在合成 AI 配音…'
    case 'animation':
      return '正在渲染思维导图动画…'
    case 'compose':
      return '正在合成最终视频与字幕…'
    default:
      return ''
  }
}

function estimateSeconds(config: VideoConfig): number {
  const base = 60
  const perDuration = config.nodeDuration * 8
  return base + perDuration
}

function estimateFileSize(config: VideoConfig, seconds: number): number {
  const factor =
    config.resolution === '4k'
      ? 1.4
      : config.resolution === '2k'
        ? 0.9
        : config.resolution === '1080p'
          ? 0.5
          : 0.25
  return Math.round(seconds * 1024 * 1024 * factor)
}
