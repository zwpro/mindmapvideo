<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import {
  ArrowLeft,
  ArrowRight,
  Sparkles,
  Volume2,
  Music2,
  Palette,
  Sliders,
  Play,
} from 'lucide-vue-next'
import PageShell from '@/components/layout/PageShell.vue'
import AppButton from '@/components/ui/AppButton.vue'
import AppCard from '@/components/ui/AppCard.vue'
import AppStepper from '@/components/ui/AppStepper.vue'
import AppBadge from '@/components/ui/AppBadge.vue'
import { useProjectStore } from '@/stores/projects'
import { useTaskStore } from '@/stores/tasks'
import { useUserStore } from '@/stores/user'
import {
  ANIMATION_STYLES,
  BGM_OPTIONS,
  RATIOS,
  RESOLUTIONS,
  THEME_STYLES,
  VOICES,
} from '@/lib/constants'
import type { VideoConfig } from '@/types'
import { cn } from '@/lib/utils'

const route = useRoute()
const router = useRouter()
const projects = useProjectStore()
const tasks = useTaskStore()
const user = useUserStore()

const projectId = computed(() => route.params.projectId as string)
const project = computed(() => projects.byId(projectId.value))

const config = reactive<VideoConfig>({
  animationStyle: 'unfold',
  resolution: '720p',
  ratio: '16:9',
  nodeDuration: 4,
  voice: { id: 'voice-aurora', speed: 1, volume: 0.9 },
  bgm: { id: 'bgm-ambient', volume: 1 },
  theme: 'tech',
})

const STEPS = [
  { key: 'outline', label: '大纲生成' },
  { key: 'config', label: '视频配置' },
  { key: 'progress', label: '生成视频' },
  { key: 'preview', label: '预览导出' },
]

const playingVoice = ref<string | null>(null)
const tryVoice = (id: string) => {
  playingVoice.value = id
  setTimeout(() => (playingVoice.value = null), 1400)
}

const playingBgm = ref<string | null>(null)
const tryBgm = (id: string) => {
  if (id === 'bgm-none') return
  playingBgm.value = id
  setTimeout(() => (playingBgm.value = null), 1400)
}

const estimatedDuration = computed(() => {
  const sceneCount = project.value?.scenes?.length ?? 8
  const baseSeconds = 30 + sceneCount * 15
  const m = Math.floor(baseSeconds / 60)
  const s = baseSeconds % 60
  return `${m}:${String(s).padStart(2, '0')}`
})

const submit = async () => {
  if (!project.value) return
  try {
    // 1) 把 ConfigPage 上的视频参数落到 project.config
    await projects.setConfig(projectId.value, JSON.parse(JSON.stringify(config)))

    // 2) 创建任务：后端 video_service.create_task 会同步把 task 入库 +
    //    把 project.status('generating') / task_id / video_id 一并落库后立即返回，
    //    真正的视频合成在后台 video_pipeline 里异步推进。
    //    这里 *不能* 立刻 fetchVideo —— compose 阶段才会写 video_details，
    //    早于那之前请求会 404 把整个 try 块抛飞，直接卡在 ConfigPage 不跳转。
    const task = await tasks.createTask(projectId.value)

    user.pushNotification({
      title: '视频生成已启动',
      body: `主题「${project.value.topic}」已进入生成队列`,
      level: 'info',
    })

    // 3) 立即跳到进度页，由 ProgressPage 通过轮询拿 stage 流转
    router.push({ name: 'progress', params: { taskId: task.id } })
  } catch (err) {
    console.error('[ConfigPage] createTask failed', err)
    user.pushNotification({
      title: '视频生成失败',
      body: err instanceof Error ? err.message : '未知错误',
      level: 'warning',
    })
  }
}

const setBgm = (id: string) => {
  if (id === 'bgm-none') {
    config.bgm = null
  } else {
    config.bgm = config.bgm
      ? { ...config.bgm, id }
      : { id, volume: 1 }
  }
}

onMounted(async () => {
  if (!project.value) {
    try {
      await projects.fetchOne(projectId.value)
    } catch {
      router.replace({ name: 'dashboard' })
      return
    }
  }
  if (!project.value) {
    router.replace({ name: 'dashboard' })
    return
  }
  if (project.value.config) {
    Object.assign(config, project.value.config)
  }
  // 后端 VideoConfig.bgm 默认是 None，新建项目落库后会被 Object.assign 写成 null，
  // 导致 ConfigPage 上 "不使用 BGM" 被高亮成默认值。
  // 草稿态下未提交过配置，统一兜底成 BGM_OPTIONS 的第一项（bgm-ambient）；
  // 用户主动点 "不使用 BGM" 提交后，status 会切到 generating/completed/failed，
  // 那时保留 null 才能尊重用户选择。
  if (!config.bgm && project.value.status === 'draft') {
    const first = BGM_OPTIONS[0]
    if (first && first.id !== 'bgm-none') {
      config.bgm = { id: first.id, volume: 1 }
    }
  }
  const lockedResolution = RESOLUTIONS.find((r) => r.id === config.resolution)
  if (!lockedResolution || lockedResolution.comingSoon) {
    config.resolution = '720p'
  }
})
</script>

<template>
  <PageShell hide-footer>
    <div class="container-page space-y-6 py-8">
      <!-- HEADER -->
      <div class="flex flex-col gap-4">
        <div class="flex items-center justify-between gap-3">
          <button
            class="inline-flex items-center gap-1.5 text-sm text-mist-400 hover:text-electric-400"
            @click="router.push({ name: 'outline', params: { projectId } })"
          >
            <ArrowLeft class="h-4 w-4" /> 返回大纲
          </button>
          <AppButton variant="primary" size="md" @click="submit">
            <Sparkles class="h-4 w-4" /> 开始生成视频
            <ArrowRight class="h-4 w-4" />
          </AppButton>
        </div>
        <AppStepper :steps="STEPS" :current="1" />
      </div>

      <div class="grid grid-cols-1 gap-6 lg:grid-cols-[1fr_360px]">
        <div class="space-y-6">
          <!-- 视觉主题 -->
          <AppCard>
            <div class="mb-4 flex items-center gap-2">
              <Palette class="h-4 w-4 text-electric-400" />
              <h3 class="font-display text-base font-semibold">视觉主题</h3>
            </div>
            <div class="grid grid-cols-2 gap-3 lg:grid-cols-5">
              <button
                v-for="t in THEME_STYLES"
                :key="t.id"
                :class="
                  cn(
                    'overflow-hidden rounded-xl border p-3 text-left transition-all',
                    config.theme === t.id
                      ? 'border-electric-400/60 shadow-glow-sm'
                      : 'border-zinc-200 hover:border-zinc-300',
                  )
                "
                @click="config.theme = t.id"
              >
                <div
                  class="relative mb-3 flex h-16 items-center justify-center overflow-hidden rounded-md ring-1 ring-inset ring-black/5"
                  :style="{
                    background: `linear-gradient(135deg, ${t.primary} 0%, ${t.mid} 50%, ${t.accent} 100%)`,
                  }"
                >
                  <span
                    class="font-display text-xs font-semibold tracking-wide"
                    :style="{
                      color: t.textOnCover,
                      textShadow: '0 1px 2px rgba(0,0,0,0.12)',
                    }"
                  >
                    {{ t.name }}
                  </span>
                </div>
                <div class="text-sm font-medium text-moon-50">{{ t.name }}</div>
                <p class="text-[11px] text-mist-500">{{ t.description }}</p>
              </button>
            </div>
          </AppCard>

          <!-- 视频参数 -->
          <AppCard>
            <div class="mb-4 flex items-center gap-2">
              <Sliders class="h-4 w-4 text-electric-400" />
              <h3 class="font-display text-base font-semibold">视频参数</h3>
            </div>
            <div>
              <p class="mb-2 text-xs uppercase tracking-wider text-mist-500">分辨率</p>
              <div class="flex flex-wrap gap-2">
                <button
                  v-for="r in RESOLUTIONS"
                  :key="r.id"
                  :disabled="r.comingSoon"
                  :title="r.comingSoon ? '即将开放' : ''"
                  :class="
                    cn(
                      'relative rounded-md border px-3 py-2 text-left text-xs transition-all',
                      r.comingSoon
                        ? 'cursor-not-allowed border-zinc-200 bg-zinc-50 text-mist-400 opacity-60'
                        : config.resolution === r.id
                          ? 'border-electric-400/60 bg-electric-400/10 text-electric-400'
                          : 'border-zinc-200 text-mist-400 hover:text-moon-50 hover:border-zinc-300',
                    )
                  "
                  @click="!r.comingSoon && (config.resolution = r.id)"
                >
                  <div class="flex items-center gap-1.5">
                    <span class="text-sm font-medium">{{ r.label }}</span>
                    <span
                      v-if="r.comingSoon"
                      class="rounded-full border border-electric-400/40 bg-white px-1.5 py-0.5 text-[10px] font-medium tracking-wider text-electric-400"
                    >
                      即将开放
                    </span>
                  </div>
                  <div class="text-[11px] text-mist-500">{{ r.hint }}</div>
                </button>
              </div>
            </div>
          </AppCard>

          <!-- 配音 / BGM -->
          <AppCard>
            <div class="mb-4 flex items-center gap-2">
              <Volume2 class="h-4 w-4 text-electric-400" />
              <h3 class="font-display text-base font-semibold">配音与背景音</h3>
            </div>

            <p class="mb-2 text-xs uppercase tracking-wider text-mist-500">AI 配音</p>
            <div
              class="relative overflow-hidden rounded-xl border border-dashed border-electric-400/40 bg-indigo-50/60 px-5 py-6"
            >
              <div class="flex items-start gap-4">
                <div
                  class="grid h-10 w-10 shrink-0 place-items-center rounded-lg bg-electric-400/15 text-electric-400"
                >
                  <Sparkles class="h-5 w-5" />
                </div>
                <div class="flex-1">
                  <div class="flex flex-wrap items-center gap-2">
                    <span class="font-display text-sm font-semibold text-moon-50">
                      AI 配音
                    </span>
                    <span
                      class="rounded-full border border-electric-400/40 bg-white px-2 py-0.5 text-[10px] font-medium uppercase tracking-wider text-electric-400"
                    >
                      内测中
                    </span>
                  </div>
                  <p class="mt-1 text-xs leading-relaxed text-mist-500">
                    多音色 AI 配音功能正在内测打磨中，即将上线。届时支持中英双语、多种音色与情感风格，敬请期待。
                  </p>
                </div>
              </div>
              <div
                aria-hidden="true"
                class="pointer-events-none absolute -right-8 -top-8 h-24 w-24 rounded-full bg-electric-400/10 blur-2xl"
              ></div>
            </div>

            <div class="mt-6">
              <p class="mb-2 flex items-center gap-2 text-xs uppercase tracking-wider text-mist-500">
                <Music2 class="h-3.5 w-3.5" /> 背景音乐
              </p>
              <div class="flex flex-wrap gap-2">
                <button
                  v-for="b in BGM_OPTIONS"
                  :key="b.id"
                  :class="
                    cn(
                      'rounded-full border px-3 py-1.5 text-xs transition-all',
                      (config.bgm?.id === b.id) || (b.id === 'bgm-none' && !config.bgm)
                        ? 'border-electric-400/60 bg-electric-400/10 text-electric-400'
                        : 'border-zinc-200 text-mist-400 hover:text-moon-50 hover:border-zinc-300',
                    )
                  "
                  @click="setBgm(b.id)"
                  @dblclick="tryBgm(b.id)"
                >
                  <span class="font-medium">{{ b.name }}</span>
                  <span class="ml-1 text-[11px] text-mist-500">{{ b.mood }}</span>
                </button>
              </div>
            </div>
          </AppCard>
        </div>

        <!-- SUMMARY -->
        <div class="space-y-4 lg:sticky lg:top-24 self-start">
          <AppCard>
            <h3 class="mb-3 font-display text-base font-semibold">配置概览</h3>
            <div class="space-y-3 text-sm">
              <div class="flex items-center justify-between">
                <span class="text-mist-500">主题</span>
                <span class="text-moon-50 line-clamp-1 max-w-[60%] text-right">{{ project?.topic }}</span>
              </div>
              <div class="flex items-center justify-between">
                <span class="text-mist-500">视觉主题</span>
                <AppBadge tone="electric">
                  {{ THEME_STYLES.find((t) => t.id === config.theme)?.name }}
                </AppBadge>
              </div>
              <div class="flex items-center justify-between">
                <span class="text-mist-500">分辨率</span>
                <span class="text-moon-50">{{ config.resolution.toUpperCase() }}</span>
              </div>
              <div class="flex items-center justify-between">
                <span class="text-mist-500">配音</span>
                <span class="text-moon-50">内测中</span>
              </div>
              <div class="my-3 h-px bg-zinc-200" />
              <div class="flex items-center justify-between text-base">
                <span class="text-mist-400">预计时长</span>
                <span class="font-display font-semibold text-electric-400">
                  {{ estimatedDuration }}
                </span>
              </div>
            </div>

            <AppButton variant="primary" block size="md" class="mt-5" @click="submit">
              <Sparkles class="h-4 w-4" /> 开始生成视频
            </AppButton>
            <p class="mt-3 text-center text-[11px] text-mist-500">
              生成后可在工作台和用户中心继续查看
            </p>
          </AppCard>
        </div>
      </div>
    </div>
  </PageShell>
</template>
