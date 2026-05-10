import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useProjectStore } from '@/stores/projects'
import { useUserStore } from '@/stores/user'

export function useCreateProject() {
  const router = useRouter()
  const projects = useProjectStore()
  const user = useUserStore()
  const creating = ref(false)
  const error = ref<string | null>(null)

  const createAndGo = async (topic: string) => {
    const trimmed = topic.trim()
    if (!trimmed) return null
    if (creating.value) return null
    creating.value = true
    error.value = null
    try {
      const project = await projects.create(trimmed)
      await router.push({ name: 'outline', params: { projectId: project.id } })
      return project
    } catch (err) {
      const message = err instanceof Error ? err.message : '创建项目失败'
      error.value = message
      user.pushNotification({ title: '创建项目失败', body: message, level: 'warning' })
      return null
    } finally {
      creating.value = false
    }
  }

  return { createAndGo, creating, error }
}
