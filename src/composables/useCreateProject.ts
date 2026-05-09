import { useRouter } from 'vue-router'
import { useProjectStore } from '@/stores/projects'

export function useCreateProject() {
  const router = useRouter()
  const projects = useProjectStore()

  const createAndGo = (topic: string) => {
    const trimmed = topic.trim()
    if (!trimmed) return null
    const project = projects.create(trimmed)
    router.push({ name: 'outline', params: { projectId: project.id } })
    return project
  }

  return { createAndGo }
}
