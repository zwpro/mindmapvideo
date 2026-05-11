<script setup lang="ts">
import { computed, onActivated, onMounted, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import {
  Search,
  ArrowRight,
  Wand2,
  FolderKanban,
  CheckCircle2,
  Loader2,
  Trash2,
  Eye,
  Pencil,
  Plus,
  Sparkles,
} from 'lucide-vue-next'
import PageShell from '@/components/layout/PageShell.vue'
import AppInput from '@/components/ui/AppInput.vue'
import AppButton from '@/components/ui/AppButton.vue'
import AppCard from '@/components/ui/AppCard.vue'
import AppBadge from '@/components/ui/AppBadge.vue'
import { useProjectStore } from '@/stores/projects'
import { useUserStore } from '@/stores/user'
import { useCreateProject } from '@/composables/useCreateProject'
import { formatRelative } from '@/lib/format'
import type { Project, ProjectStatus } from '@/types'

const router = useRouter()
const projects = useProjectStore()
const user = useUserStore()
const { createAndGo } = useCreateProject()

const topic = ref('')
const keyword = ref('')
const statusFilter = ref<'all' | ProjectStatus>('all')
const loadError = ref<string | null>(null)

// 每次进入工作台都强制拉一次列表：projects.fetchList 默认有 "loaded once" 缓存，
// 这里显式传 force=true 绕开它，否则切到其它页再回来看到的是旧数据。
const reloadList = async () => {
  try {
    await projects.fetchList(true)
    loadError.value = null
  } catch (err) {
    loadError.value = err instanceof Error ? err.message : '加载项目失败'
  }
}

onMounted(reloadList)
// 给未来可能套上 <keep-alive> 的场景留兜底：组件被激活时也刷新
onActivated(reloadList)

// 切换分类（statusFilter）时重新调用列表接口
// flush:'post' 确保按钮 UI 状态先翻新再发请求
watch(statusFilter, reloadList, { flush: 'post' })

const filtered = computed(() => {
  const k = keyword.value.trim().toLowerCase()
  return projects.sorted.filter((p) => {
    const matchKeyword = !k || p.topic.toLowerCase().includes(k)
    const matchStatus =
      statusFilter.value === 'all' || p.status === statusFilter.value
    return matchKeyword && matchStatus
  })
})

const submit = (val?: string) => {
  const v = (val ?? topic.value).trim()
  if (!v) return
  topic.value = ''
  void createAndGo(v)
}

const filters: Array<{ key: 'all' | ProjectStatus; label: string }> = [
  { key: 'all', label: '全部' },
  { key: 'draft', label: '草稿' },
  { key: 'generating', label: '生成中' },
  { key: 'completed', label: '已完成' },
  { key: 'failed', label: '失败' },
]

const statusToneMap: Record<ProjectStatus, 'neutral' | 'warning' | 'success' | 'danger'> = {
  draft: 'neutral',
  generating: 'warning',
  completed: 'success',
  failed: 'danger',
}

const statusLabelMap: Record<ProjectStatus, string> = {
  draft: '草稿',
  generating: '生成中',
  completed: '已完成',
  failed: '失败',
}

const openProject = (p: Project) => {
  if (p.status === 'completed' && p.videoId) {
    router.push({ name: 'preview', params: { videoId: p.videoId } })
  } else if (p.status === 'generating' && p.taskId) {
    router.push({ name: 'progress', params: { taskId: p.taskId } })
  } else {
    router.push({ name: 'outline', params: { projectId: p.id } })
  }
}

const editProject = (p: Project) => {
  router.push({ name: 'outline', params: { projectId: p.id } })
}

const removeProject = async (p: Project) => {
  if (!confirm(`确定删除项目「${p.topic}」吗？此操作不可撤销。`)) return
  try {
    await projects.remove(p.id)
  } catch (err) {
    const message = err instanceof Error ? err.message : '删除失败'
    user.pushNotification({ title: '删除失败', body: message, level: 'warning' })
  }
}
</script>

<template>
  <PageShell>
    <!-- HEADER -->
    <section class="relative">
      <div class="absolute inset-0 bg-hero-glow opacity-60" />
      <div class="container-page relative pt-12 pb-8">
        <div class="flex flex-col gap-6 lg:flex-row lg:items-end lg:justify-between">
          <div>
            <h1 class="font-display text-h2 font-semibold">工作台</h1>
            <p class="mt-2 text-sm text-mist-400">
              管理你的全部分镜视频项目，从这里开始下一支创作。
            </p>
          </div>
          <div class="w-full max-w-xl">
            <AppInput
              v-model="topic"
              size="md"
              placeholder="输入主题，立刻开始一个新项目…"
              @submit="(v) => submit(v)"
            >
              <template #prefix>
                <Wand2 class="h-4 w-4 text-electric-400" />
              </template>
              <template #suffix>
                <AppButton variant="primary" size="sm" @click="submit()">
                  <Plus class="h-4 w-4" /> 创建
                </AppButton>
              </template>
            </AppInput>
          </div>
        </div>

        <!-- STATS -->
        <div class="mt-8 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          <AppCard class="!p-5">
            <div class="flex items-center justify-between">
              <span class="text-xs uppercase tracking-wider text-mist-500"
                >全部项目</span
              >
              <FolderKanban class="h-4 w-4 text-mist-400" />
            </div>
            <div class="mt-3 font-display text-3xl font-semibold">
              {{ projects.counts.total }}
            </div>
          </AppCard>
          <AppCard class="!p-5">
            <div class="flex items-center justify-between">
              <span class="text-xs uppercase tracking-wider text-mist-500"
                >已完成视频</span
              >
              <CheckCircle2 class="h-4 w-4 text-success" />
            </div>
            <div class="mt-3 font-display text-3xl font-semibold text-success">
              {{ projects.counts.completed }}
            </div>
          </AppCard>
          <AppCard class="!p-5">
            <div class="flex items-center justify-between">
              <span class="text-xs uppercase tracking-wider text-mist-500"
                >生成中</span
              >
              <Loader2 class="h-4 w-4 animate-spin text-warning" />
            </div>
            <div class="mt-3 font-display text-3xl font-semibold text-warning">
              {{ projects.counts.generating }}
            </div>
          </AppCard>
          <AppCard class="!p-5">
            <div class="flex items-center justify-between">
              <span class="text-xs uppercase tracking-wider text-mist-500"
                >草稿</span
              >
              <Sparkles class="h-4 w-4 text-electric-400" />
            </div>
            <div class="mt-3 font-display text-3xl font-semibold text-electric-400">
              {{ projects.counts.draft }}
            </div>
          </AppCard>
        </div>
      </div>
    </section>

    <!-- LIST -->
    <section class="container-page pb-20">
      <div class="mb-6 flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
        <div class="flex flex-wrap gap-2">
          <button
            v-for="f in filters"
            :key="f.key"
            class="rounded-full border px-3 py-1 text-xs transition-all"
            :class="
              statusFilter === f.key
                ? 'border-electric-400/60 bg-electric-400/10 text-electric-400'
                : 'border-zinc-200 bg-white text-mist-400 hover:text-moon-50 hover:border-zinc-300'
            "
            @click="statusFilter = f.key"
          >
            {{ f.label }}
          </button>
        </div>
        <div class="md:w-72">
          <AppInput v-model="keyword" size="sm" placeholder="搜索项目主题…">
            <template #prefix>
              <Search class="h-4 w-4 text-mist-400" />
            </template>
          </AppInput>
        </div>
      </div>

      <!-- EMPTY -->
      <AppCard v-if="filtered.length === 0" class="text-center !py-20">
        <div
          class="mx-auto mb-6 flex h-16 w-16 items-center justify-center rounded-2xl border border-electric-400/30 bg-electric-400/10 text-3xl"
        >
          ✨
        </div>
        <h3 class="font-display text-lg font-semibold">
          还没有匹配的项目，开始一个吧
        </h3>
        <p class="mt-2 text-sm text-mist-400">
          输入一个你想讲的主题，几秒钟内 AI 就会生成完整大纲。
        </p>
        <div class="mx-auto mt-6 max-w-md">
          <AppInput
            v-model="topic"
            size="md"
            placeholder="例如：宇宙的起源"
            @submit="(v) => submit(v)"
          >
            <template #prefix>
              <Wand2 class="h-4 w-4 text-electric-400" />
            </template>
            <template #suffix>
              <AppButton variant="primary" size="sm" @click="submit()">
                创建 <ArrowRight class="h-4 w-4" />
              </AppButton>
            </template>
          </AppInput>
        </div>
      </AppCard>

      <div v-else class="grid gap-6 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
        <AppCard
          v-for="p in filtered"
          :key="p.id"
          interactive
          :padded="false"
          class="group overflow-hidden"
          @click="openProject(p)"
        >
          <div class="relative aspect-[16/10] overflow-hidden">
            <img
              :src="p.thumbnailUrl"
              :alt="p.topic"
              class="h-full w-full object-cover transition-transform duration-500 group-hover:scale-105"
            />
            <div class="absolute inset-0 bg-gradient-to-t from-zinc-900/60 to-transparent" />
            <span class="absolute left-3 top-3">
              <AppBadge :tone="statusToneMap[p.status]" dot>{{
                statusLabelMap[p.status]
              }}</AppBadge>
            </span>

            <!-- HOVER ACTIONS -->
            <div
              class="absolute inset-x-3 bottom-3 flex translate-y-2 items-center gap-2 opacity-0 transition-all group-hover:translate-y-0 group-hover:opacity-100"
            >
              <AppButton
                variant="primary"
                size="sm"
                @click.stop="openProject(p)"
              >
                <Eye class="h-3.5 w-3.5" />
                {{ p.status === 'completed' ? '观看' : '继续' }}
              </AppButton>
              <AppButton
                variant="secondary"
                size="sm"
                @click.stop="editProject(p)"
              >
                <Pencil class="h-3.5 w-3.5" /> 编辑
              </AppButton>
              <AppButton
                variant="ghost"
                size="sm"
                @click.stop="removeProject(p)"
                aria-label="删除"
              >
                <Trash2 class="h-3.5 w-3.5 text-danger" />
              </AppButton>
            </div>
          </div>
          <div class="space-y-1 p-5">
            <h3 class="line-clamp-1 font-display text-base font-semibold text-moon-50">
              {{ p.topic }}
            </h3>
            <p class="text-xs text-mist-500">
              更新于 {{ formatRelative(p.updatedAt) }}
            </p>
          </div>
        </AppCard>
      </div>
    </section>
  </PageShell>
</template>
