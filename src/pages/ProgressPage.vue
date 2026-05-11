<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ArrowLeft, Clapperboard, Sparkles } from 'lucide-vue-next'
import PageShell from '@/components/layout/PageShell.vue'
import AppCard from '@/components/ui/AppCard.vue'
import AppButton from '@/components/ui/AppButton.vue'
import AppStepper from '@/components/ui/AppStepper.vue'
import { useTaskStore } from '@/stores/tasks'
import { useProjectStore } from '@/stores/projects'

const route = useRoute()
const router = useRouter()
const tasks = useTaskStore()
const projects = useProjectStore()

const taskId = computed(() => route.params.taskId as string)
const task = computed(() => tasks.taskById(taskId.value))
const project = computed(() =>
  task.value ? projects.byId(task.value.projectId) : null,
)

const STEPS = [
  { key: 'outline', label: '大纲生成' },
  { key: 'config', label: '视频配置' },
  { key: 'progress', label: '生成视频' },
  { key: 'preview', label: '预览导出' },
]

// 跳转预览页的目标 videoId 既可能来自 task，也可能来自 project
const resolvedVideoId = computed(
  () => task.value?.videoId || project.value?.videoId || null,
)

// 防止 watch 在同一个任务上反复 push
let navigated = false
const tryNavigateToPreview = () => {
  if (navigated) return
  if (task.value?.stage !== 'done') return
  const vid = resolvedVideoId.value
  if (!vid) return
  navigated = true
  setTimeout(() => {
    router.replace({ name: 'preview', params: { videoId: vid } })
  }, 600)
}

// 同时监听 stage 和 videoId：
// - 刷新页面落在已完成的任务上时（stage 不再变化）也能触发跳转 → immediate: true
// - stage 已经是 done、但 project.videoId 还没回填时，等 videoId 出现后再跳
watch(
  () => [task.value?.stage, resolvedVideoId.value] as const,
  () => tryNavigateToPreview(),
  { immediate: true },
)

// 后端 video_pipeline 异步推进 stage，前端只轮询 stage 字段，
// done/failed 后停止轮询；离开页面时清理定时器。
let pollTimer: ReturnType<typeof setInterval> | null = null

const stopPolling = () => {
  if (pollTimer) {
    clearInterval(pollTimer)
    pollTimer = null
  }
}

const tickOnce = async () => {
  try {
    const t = await tasks.fetchTask(taskId.value)
    if (t.stage === 'done' || t.stage === 'failed') {
      stopPolling()
      if (t.stage === 'done') {
        // 完成时刷新一下 project，以便拿到后端最终落库的 videoId
        if (!project.value?.videoId) {
          projects.fetchOne(t.projectId).catch(() => undefined)
        }
        if (t.videoId && !tasks.videoById(t.videoId)) {
          tasks.fetchVideo(t.videoId).catch(() => undefined)
        }
      }
    }
  } catch {
    // 间歇网络错误不要直接踢回 dashboard，等下次 tick
  }
}

onMounted(async () => {
  try {
    const t = await tasks.fetchTask(taskId.value)
    if (!projects.byId(t.projectId)) {
      await projects.fetchOne(t.projectId).catch(() => undefined)
    }
    if (t.videoId && !tasks.videoById(t.videoId)) {
      tasks.fetchVideo(t.videoId).catch(() => undefined)
    }
    if (t.stage === 'done') {
      // 落在“已完成”的任务上：可能 project 里还没有 videoId，需要再拉一次
      if (!project.value?.videoId) {
        await projects.fetchOne(t.projectId).catch(() => undefined)
      }
      tryNavigateToPreview()
    } else if (t.stage !== 'failed') {
      pollTimer = setInterval(tickOnce, 2000)
    }
  } catch {
    router.replace({ name: 'dashboard' })
  }
})

onBeforeUnmount(stopPolling)
</script>

<template>
  <PageShell hide-footer>
    <div class="container-page space-y-6 py-8">
      <div class="flex flex-col gap-4">
        <button
          class="inline-flex w-fit items-center gap-1.5 text-sm text-mist-400 hover:text-electric-400"
          @click="router.push('/dashboard')"
        >
          <ArrowLeft class="h-4 w-4" /> 返回工作台
        </button>
        <AppStepper :steps="STEPS" :current="2" />
      </div>

      <AppCard class="!p-12 text-center">
        <div
          class="mx-auto flex h-20 w-20 items-center justify-center rounded-full border border-electric-400/40 bg-electric-400/10 text-electric-400 shadow-glow animate-pulse-ring"
        >
          <Clapperboard class="h-9 w-9" />
        </div>
        <h2 class="mt-6 font-display text-h3 font-semibold">
          <template v-if="task?.stage === 'failed'">视频生成失败</template>
          <template v-else-if="task?.stage === 'done'">渲染完成，正在跳转预览页…</template>
          <template v-else>AI 正在为你打造视频</template>
        </h2>
        <p class="mt-2 text-sm text-mist-400">
          主题：<span class="text-moon-50">{{ project?.topic }}</span>
        </p>
        <p
          v-if="task && task.stage !== 'done' && task.stage !== 'failed'"
          class="mt-3 inline-flex items-center gap-2 text-xs text-mist-500"
        >
          <span class="relative flex h-2 w-2">
            <span class="absolute inline-flex h-full w-full animate-ping rounded-full bg-electric-400 opacity-75"></span>
            <span class="relative inline-flex h-2 w-2 rounded-full bg-electric-400"></span>
          </span>
          生成中，请稍候…
        </p>
      </AppCard>

      <AppCard
        v-if="task?.stage === 'failed'"
        class="!p-5 border-rose-500/40 bg-rose-500/5"
      >
        <div class="text-sm font-semibold text-rose-500">合成失败</div>
        <p class="mt-2 break-all text-xs text-mist-500">
          {{ task?.error || '未知错误，请联系管理员或检查后端日志。' }}
        </p>
      </AppCard>

      <AppCard class="!p-6">
        <div class="flex flex-col items-center justify-between gap-4 md:flex-row">
          <div class="flex items-center gap-3 text-sm text-mist-400">
            <Sparkles class="h-4 w-4 text-electric-400" />
            可以离开此页面，生成完成后会在工作台与通知中心同步状态。
          </div>
          <AppButton variant="secondary" size="md" @click="router.push('/dashboard')">
            返回工作台继续创作
          </AppButton>
        </div>
      </AppCard>
    </div>
  </PageShell>
</template>
