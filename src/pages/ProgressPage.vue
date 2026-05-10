<script setup lang="ts">
import { computed, onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import {
  ArrowLeft,
  Mic2,
  Wand2,
  Film,
  CheckCircle2,
  Clapperboard,
  Sparkles,
} from 'lucide-vue-next'
import PageShell from '@/components/layout/PageShell.vue'
import AppCard from '@/components/ui/AppCard.vue'
import AppButton from '@/components/ui/AppButton.vue'
import AppStepper from '@/components/ui/AppStepper.vue'
import { useTaskStore } from '@/stores/tasks'
import { useProjectStore } from '@/stores/projects'
import type { GenerationStage } from '@/types'
import { cn } from '@/lib/utils'

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

const stages: Array<{
  key: GenerationStage
  label: string
  hint: string
  icon: typeof Mic2
}> = [
  { key: 'voice', label: '配音合成', hint: '为每个节点生成 AI 解说', icon: Mic2 },
  { key: 'animation', label: '动画渲染', hint: '逐节点生成思维导图动画', icon: Wand2 },
  { key: 'compose', label: '视频合成', hint: '合并配音、动画与字幕', icon: Film },
  { key: 'done', label: '渲染完成', hint: '即可观看 / 下载 / 分享', icon: CheckCircle2 },
]

const stageIndex = computed(() => {
  if (!task.value) return 0
  return stages.findIndex((s) => s.key === task.value!.stage)
})

const overallProgress = computed(() => {
  if (!task.value) return 0
  if (task.value.stage === 'done') return 100
  const idx = stageIndex.value
  const localProgress = task.value.progress / 100
  return Math.min(99, ((idx + localProgress) / 3) * 100)
})

watch(
  () => task.value?.stage,
  (stage) => {
    if (stage === 'done' && project.value?.videoId) {
      setTimeout(() => {
        router.replace({
          name: 'preview',
          params: { videoId: project.value!.videoId! },
        })
      }, 600)
    }
  },
)

onMounted(async () => {
  try {
    const t = await tasks.fetchTask(taskId.value)
    if (!projects.byId(t.projectId)) {
      await projects.fetchOne(t.projectId).catch(() => undefined)
    }
    if (t.videoId && !tasks.videoById(t.videoId)) {
      tasks.fetchVideo(t.videoId).catch(() => undefined)
    }
  } catch {
    router.replace({ name: 'dashboard' })
  }
})
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

      <AppCard class="!p-10 text-center">
        <div
          class="mx-auto flex h-20 w-20 items-center justify-center rounded-full border border-electric-400/40 bg-electric-400/10 text-electric-400 shadow-glow animate-pulse-ring"
        >
          <Clapperboard class="h-9 w-9" />
        </div>
        <h2 class="mt-6 font-display text-h3 font-semibold">
          AI 正在为你打造视频
        </h2>
        <p class="mt-2 text-sm text-mist-400">
          主题：<span class="text-moon-50">{{ project?.topic }}</span>
        </p>

        <div class="mx-auto mt-8 max-w-xl">
          <div class="flex items-center justify-between text-xs">
            <span class="text-mist-400">总体进度</span>
            <span class="font-display text-electric-400">
              {{ Math.floor(overallProgress) }}%
            </span>
          </div>
          <div class="mt-2 h-2 overflow-hidden rounded-full bg-zinc-100">
            <div
              class="h-full bg-gradient-to-r from-electric-400 to-electric-600 transition-all duration-500"
              :style="{ width: overallProgress + '%' }"
            />
          </div>
          <p class="mt-3 text-xs text-mist-500">
            <template v-if="task && task.stage !== 'done'">
              当前阶段：{{ stages[stageIndex]?.label }} · 子任务进度
              {{ task.progress }}%
            </template>
            <template v-else>渲染完成，正在跳转预览页…</template>
          </p>
        </div>
      </AppCard>

      <div class="grid gap-4 md:grid-cols-4">
        <AppCard
          v-for="(s, i) in stages"
          :key="s.key"
          :class="
            cn(
              '!p-5 transition-all',
              i < stageIndex && 'border-electric-400/40 bg-electric-400/5',
              i === stageIndex && 'border-electric-400/60 shadow-glow-sm',
              i > stageIndex && 'opacity-60',
            )
          "
        >
          <div class="flex items-center justify-between">
            <span
              :class="
                cn(
                  'grid h-9 w-9 place-items-center rounded-md border',
                  i <= stageIndex
                    ? 'border-electric-400/40 bg-electric-400/10 text-electric-400'
                    : 'border-zinc-200 bg-zinc-100 text-mist-400',
                )
              "
            >
              <component :is="s.icon" class="h-4 w-4" />
            </span>
            <span
              :class="
                cn(
                  'rounded-full px-2 py-0.5 text-[11px]',
                  i < stageIndex && 'bg-success/15 text-success',
                  i === stageIndex && 'bg-warning/15 text-warning animate-pulse',
                  i > stageIndex && 'bg-zinc-100 text-mist-500',
                )
              "
            >
              <template v-if="i < stageIndex">已完成</template>
              <template v-else-if="i === stageIndex">进行中</template>
              <template v-else>等待中</template>
            </span>
          </div>
          <div class="mt-4">
            <h4 class="font-display text-sm font-semibold text-moon-50">
              {{ s.label }}
            </h4>
            <p class="mt-1 text-xs text-mist-500">{{ s.hint }}</p>
          </div>
          <div v-if="i === stageIndex && task" class="mt-4">
            <div class="h-1.5 overflow-hidden rounded-full bg-zinc-100">
              <div
                class="h-full animate-pulse bg-electric-400 transition-all"
                :style="{ width: task.progress + '%' }"
              />
            </div>
          </div>
        </AppCard>
      </div>

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
