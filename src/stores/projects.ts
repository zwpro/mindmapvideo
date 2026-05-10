import { defineStore } from 'pinia'
import type { OutlineNode, Project, ProjectStatus, Scene, VideoConfig } from '@/types'
import { projectApi } from '@/lib/api'

interface State {
  projects: Project[]
  loading: boolean
  loaded: boolean
  error: string | null
}

export const useProjectStore = defineStore('projects', {
  state: (): State => ({
    projects: [],
    loading: false,
    loaded: false,
    error: null,
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
    upsert(project: Project) {
      const idx = this.projects.findIndex((p) => p.id === project.id)
      if (idx >= 0) this.projects.splice(idx, 1, project)
      else this.projects.unshift(project)
    },

    async fetchList(force = false): Promise<Project[]> {
      if (this.loaded && !force) return this.projects
      this.loading = true
      this.error = null
      try {
        const list = await projectApi.list()
        this.projects = list
        this.loaded = true
        return list
      } catch (err) {
        this.error = (err as Error).message
        throw err
      } finally {
        this.loading = false
      }
    },

    async fetchOne(id: string): Promise<Project> {
      const project = await projectApi.get(id)
      this.upsert(project)
      return project
    },

    async create(topic: string): Promise<Project> {
      const project = await projectApi.create({ topic })
      this.upsert(project)
      return project
    },

    async update(id: string, patch: Partial<Project>): Promise<Project> {
      const project = await projectApi.update(id, patch)
      this.upsert(project)
      return project
    },

    setOutline(id: string, outline: OutlineNode) {
      return this.update(id, { outline })
    },
    setScenes(id: string, scenes: Scene[]) {
      return this.update(id, { scenes })
    },
    setConfig(id: string, config: VideoConfig) {
      return this.update(id, { config })
    },
    setStatus(id: string, status: ProjectStatus) {
      return this.update(id, { status })
    },

    async remove(id: string): Promise<void> {
      await projectApi.delete(id)
      const idx = this.projects.findIndex((p) => p.id === id)
      if (idx >= 0) this.projects.splice(idx, 1)
    },
  },
})
