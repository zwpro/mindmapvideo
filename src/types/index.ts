export type ProjectStatus = 'draft' | 'generating' | 'completed' | 'failed'

export type AnimationStyle = 'unfold' | 'roam' | 'focus' | 'overview'

export type Resolution = '720p' | '1080p' | '2k' | '4k'

export type Ratio = '16:9' | '9:16' | '1:1'

export type ThemeStyle = 'minimal' | 'tech' | 'academic' | 'cartoon' | 'business'

export type GenerationStage = 'voice' | 'animation' | 'compose' | 'done' | 'failed'

export interface OutlineNode {
  id: string
  parentId: string | null
  title: string
  note?: string
  depth: number
  children: OutlineNode[]
}

export interface Scene {
  id: string
  index: number
  title: string
  content: string
  note?: string
}

export interface VideoConfig {
  animationStyle: AnimationStyle
  resolution: Resolution
  ratio: Ratio
  nodeDuration: number
  voice: {
    id: string
    speed: number
    volume: number
  } | null
  bgm: {
    id: string
    volume: number
  } | null
  theme: ThemeStyle
}

export interface Project {
  id: string
  userId: string
  topic: string
  status: ProjectStatus
  thumbnailUrl: string
  outline: OutlineNode | null
  scenes: Scene[] | null
  config: VideoConfig
  videoId?: string
  taskId?: string
  createdAt: string
  updatedAt: string
}

export interface VideoTask {
  id: string
  projectId: string
  stage: GenerationStage
  progress: number
  startedAt: string
  finishedAt?: string
  error?: string
  videoId?: string
}

export interface VideoDetail {
  id: string
  projectId: string
  taskId: string
  url: string
  thumbnailUrl: string
  duration: number
  resolution: Resolution
  ratio: Ratio
  fileSize: number
  createdAt: string
}

export interface AdminUser {
  id: 'admin'
  nickname: string
  avatarUrl: string
  bio: string
  role: 'admin'
}

export interface AppNotification {
  id: string
  title: string
  body: string
  level: 'info' | 'success' | 'warning'
  read: boolean
  createdAt: string
  link?: string
}
