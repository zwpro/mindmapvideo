import { defineStore } from 'pinia'
import { nanoid } from 'nanoid'
import type { OutlineNode, Project, ProjectStatus, Scene, VideoConfig } from '@/types'
import { DEFAULT_VIDEO_CONFIG } from '@/lib/constants'

interface State {
  projects: Project[]
}

const seed: Project[] = [
  {
    id: 'proj-demo-1',
    userId: 'admin',
    topic: '人工智能发展史',
    status: 'completed',
    thumbnailUrl:
      'https://trae-api-cn.mchost.guru/api/ide/v1/text_to_image?prompt=futuristic%20mindmap%20visualization%20about%20artificial%20intelligence%20history%2C%20deep%20navy%20background%2C%20cyan%20neon%20nodes%2C%20glowing%20connections&image_size=landscape_16_9',
    outline: null,
    scenes: null,
    config: { ...DEFAULT_VIDEO_CONFIG },
    videoId: 'video-demo-1',
    createdAt: new Date(Date.now() - 86_400_000 * 3).toISOString(),
    updatedAt: new Date(Date.now() - 86_400_000 * 1).toISOString(),
  },
  {
    id: 'proj-demo-2',
    userId: 'admin',
    topic: 'Python 入门学习路线',
    status: 'draft',
    thumbnailUrl:
      'https://trae-api-cn.mchost.guru/api/ide/v1/text_to_image?prompt=mindmap%20diagram%20about%20python%20learning%20roadmap%2C%20dark%20theme%2C%20mint%20green%20highlights%2C%20clean%20typography&image_size=landscape_16_9',
    outline: null,
    scenes: null,
    config: { ...DEFAULT_VIDEO_CONFIG },
    createdAt: new Date(Date.now() - 86_400_000 * 5).toISOString(),
    updatedAt: new Date(Date.now() - 86_400_000 * 2).toISOString(),
  },
  {
    id: 'proj-demo-3',
    userId: 'admin',
    topic: '区块链基础原理',
    status: 'generating',
    thumbnailUrl:
      'https://trae-api-cn.mchost.guru/api/ide/v1/text_to_image?prompt=abstract%20blockchain%20mindmap%20concept%20art%2C%20glowing%20chain%20links%2C%20cyberpunk%20palette%2C%20cinematic%20lighting&image_size=landscape_16_9',
    outline: null,
    scenes: null,
    config: { ...DEFAULT_VIDEO_CONFIG },
    createdAt: new Date(Date.now() - 86_400_000 * 1).toISOString(),
    updatedAt: new Date(Date.now() - 3_600_000).toISOString(),
  },
]

export const useProjectStore = defineStore('projects', {
  state: (): State => ({
    projects: seed,
  }),
  getters: {
    byId: (s) => (id: string) => s.projects.find((p) => p.id === id) || null,
    sorted: (s) =>
      [...s.projects].sort(
        (a, b) =>
          new Date(b.updatedAt).getTime() - new Date(a.updatedAt).getTime(),
      ),
    counts: (s) => ({
      total: s.projects.length,
      completed: s.projects.filter((p) => p.status === 'completed').length,
      generating: s.projects.filter((p) => p.status === 'generating').length,
      draft: s.projects.filter((p) => p.status === 'draft').length,
      failed: s.projects.filter((p) => p.status === 'failed').length,
    }),
  },
  actions: {
    create(topic: string): Project {
      const id = `proj-${nanoid(8)}`
      const now = new Date().toISOString()
      const project: Project = {
        id,
        userId: 'admin',
        topic,
        status: 'draft',
        thumbnailUrl: thumbnailFor(topic),
        outline: null,
        scenes: null,
        config: { ...DEFAULT_VIDEO_CONFIG },
        createdAt: now,
        updatedAt: now,
      }
      this.projects.unshift(project)
      return project
    },
    update(id: string, patch: Partial<Project>) {
      const target = this.projects.find((p) => p.id === id)
      if (!target) return
      Object.assign(target, patch, { updatedAt: new Date().toISOString() })
    },
    setOutline(id: string, outline: OutlineNode) {
      this.update(id, { outline })
    },
    setScenes(id: string, scenes: Scene[]) {
      this.update(id, { scenes })
    },
    setConfig(id: string, config: VideoConfig) {
      this.update(id, { config })
    },
    setStatus(id: string, status: ProjectStatus) {
      this.update(id, { status })
    },
    remove(id: string) {
      const idx = this.projects.findIndex((p) => p.id === id)
      if (idx >= 0) this.projects.splice(idx, 1)
    },
  },
  persist: {
    key: 'mindmap.projects',
  },
})

function thumbnailFor(topic: string): string {
  const prompt = encodeURIComponent(
    `mindmap concept illustration about ${topic}, deep navy background, cyan and orange neon highlights, glowing nodes connected by curves`,
  )
  return `https://trae-api-cn.mchost.guru/api/ide/v1/text_to_image?prompt=${prompt}&image_size=landscape_16_9`
}
