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
import { startVideoGeneration } from '@/services/videoMock'
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

const projectId = computed(() => route.params.projectId as string)
const project = computed(() => projects.byId(projectId.value))

const config = reactive<VideoConfig>({
  animationStyle: 'unfold',
  resolution: '1080p',
  ratio: '16:9',
  nodeDuration: 4,
  voice: { id: 'voice-aurora', speed: 1, volume: 0.9 },
  bgm: { id: 'bgm-ambient', volume: 0.4 },
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
  const baseSeconds = 60 + config.nodeDuration * 8
  const m = Math.floor(baseSeconds / 60)
  const s = baseSeconds % 60
  return `${m}:${String(s).padStart(2, '0')}`
})

const submit = () => {
  if (!project.value) return
  projects.setConfig(projectId.value, JSON.parse(JSON.stringify(config)))
  projects.setStatus(projectId.value, 'generating')

  const handle = startVideoGeneration({
    project: { ...project.value, config: { ...config } },
    onTaskCreated: (task) => {
      tasks.upsert(task)
      projects.update(projectId.value, { taskId: task.id })
    },
    onEvent: (event) => {
      const taskId = project.value?.taskId
      if (!taskId) return
      tasks.setProgress(taskId, event.stage, event.progress)
    },
    onComplete: (video) => {
      tasks.addVideo(video)
      projects.update(projectId.value, {
        videoId: video.id,
        status: 'completed',
      })
    },
  })

  router.push({ name: 'progress', params: { taskId: handle.taskId } })
}

const setBgm = (id: string) => {
  if (id === 'bgm-none') {
    config.bgm = null
  } else {
    config.bgm = config.bgm
      ? { ...config.bgm, id }
      : { id, volume: 0.4 }
  }
}

onMounted(() => {
  if (!project.value) {
    router.replace({ name: 'dashboard' })
    return
  }
  if (project.value.config) {
    Object.assign(config, project.value.config)
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
          <!-- 动画风格 -->
          <AppCard>
            <div class="mb-4 flex items-center gap-2">
              <Sparkles class="h-4 w-4 text-electric-400" />
              <h3 class="font-display text-base font-semibold">动画风格</h3>
              <span class="text-xs text-mist-500">选择视频动画的呈现方式</span>
            </div>
            <div class="grid grid-cols-2 gap-3 lg:grid-cols-4">
              <button
                v-for="s in ANIMATION_STYLES"
                :key="s.id"
                :class="
                  cn(
                    'rounded-xl border p-4 text-left transition-all',
                    config.animationStyle === s.id
                      ? 'border-electric-400/60 bg-electric-400/5 shadow-glow-sm'
                      : 'border-zinc-200 bg-zinc-50 hover:border-zinc-300',
                  )
                "
                @click="config.animationStyle = s.id"
              >
                <div class="text-2xl">{{ s.emoji }}</div>
                <div class="mt-2 font-medium text-moon-50">{{ s.name }}</div>
                <p class="mt-1 text-xs leading-relaxed text-mist-500">
                  {{ s.description }}
                </p>
              </button>
            </div>
          </AppCard>

          <!-- 视频参数 -->
          <AppCard>
            <div class="mb-4 flex items-center gap-2">
              <Sliders class="h-4 w-4 text-electric-400" />
              <h3 class="font-display text-base font-semibold">视频参数</h3>
            </div>
            <div class="grid gap-6 md:grid-cols-2">
              <div>
                <p class="mb-2 text-xs uppercase tracking-wider text-mist-500">分辨率</p>
                <div class="flex flex-wrap gap-2">
                  <button
                    v-for="r in RESOLUTIONS"
                    :key="r.id"
                    :class="
                      cn(
                        'rounded-md border px-3 py-2 text-left text-xs transition-all',
                        config.resolution === r.id
                          ? 'border-electric-400/60 bg-electric-400/10 text-electric-400'
                          : 'border-zinc-200 text-mist-400 hover:text-moon-50 hover:border-zinc-300',
                      )
                    "
                    @click="config.resolution = r.id"
                  >
                    <div class="text-sm font-medium">{{ r.label }}</div>
                    <div class="text-[11px] text-mist-500">{{ r.hint }}</div>
                  </button>
                </div>
              </div>
              <div>
                <p class="mb-2 text-xs uppercase tracking-wider text-mist-500">画面比例</p>
                <div class="flex flex-wrap gap-2">
                  <button
                    v-for="r in RATIOS"
                    :key="r.id"
                    :class="
                      cn(
                        'rounded-md border px-3 py-2 text-left text-xs transition-all',
                        config.ratio === r.id
                          ? 'border-electric-400/60 bg-electric-400/10 text-electric-400'
                          : 'border-zinc-200 text-mist-400 hover:text-moon-50 hover:border-zinc-300',
                      )
                    "
                    @click="config.ratio = r.id"
                  >
                    <div class="text-sm font-medium">{{ r.label }}</div>
                    <div class="text-[11px] text-mist-500">{{ r.hint }}</div>
                  </button>
                </div>
              </div>
              <div class="md:col-span-2">
                <div class="flex items-center justify-between">
                  <p class="text-xs uppercase tracking-wider text-mist-500">
                    单节点停留时长
                  </p>
                  <span class="text-xs text-electric-400">
                    {{ config.nodeDuration }} 秒
                  </span>
                </div>
                <input
                  v-model.number="config.nodeDuration"
                  type="range"
                  min="2"
                  max="8"
                  step="1"
                  class="mt-3 w-full accent-electric-400"
                />
                <div class="mt-1 flex justify-between text-[11px] text-mist-500">
                  <span>紧凑 2s</span>
                  <span>舒缓 8s</span>
                </div>
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
            <div class="grid grid-cols-2 gap-3 lg:grid-cols-4">
              <button
                v-for="v in VOICES"
                :key="v.id"
                :class="
                  cn(
                    'flex flex-col items-start gap-2 rounded-xl border p-3 text-left transition-all',
                    config.voice?.id === v.id
                      ? 'border-electric-400/60 bg-electric-400/5'
                      : 'border-zinc-200 bg-zinc-50 hover:border-zinc-300',
                  )
                "
                @click="config.voice = config.voice ? { ...config.voice, id: v.id } : { id: v.id, speed: 1, volume: 0.9 }"
              >
                <div class="flex w-full items-center justify-between">
                  <span
                    class="grid h-8 w-8 place-items-center rounded-md font-display text-sm font-semibold"
                    :style="{ backgroundColor: v.color, color: '#0B1A2A' }"
                  >
                    {{ v.name[0] }}
                  </span>
                  <button
                    class="text-mist-400 transition-colors hover:text-electric-400"
                    aria-label="试听"
                    @click.stop="tryVoice(v.id)"
                  >
                    <Play
                      class="h-4 w-4"
                      :class="playingVoice === v.id && 'text-electric-400 animate-pulse'"
                    />
                  </button>
                </div>
                <div>
                  <div class="text-sm font-medium text-moon-50">
                    {{ v.name }}
                    <span class="ml-1 text-[11px] text-mist-500">{{ v.gender }}</span>
                  </div>
                  <p class="text-[11px] text-mist-500">{{ v.description }}</p>
                </div>
              </button>
            </div>

            <div class="mt-5 grid gap-4 md:grid-cols-2">
              <div v-if="config.voice">
                <div class="flex items-center justify-between text-xs">
                  <span class="text-mist-500">语速</span>
                  <span class="text-electric-400">{{ config.voice.speed.toFixed(1) }}x</span>
                </div>
                <input
                  v-model.number="config.voice.speed"
                  type="range"
                  min="0.6"
                  max="1.6"
                  step="0.1"
                  class="mt-2 w-full accent-electric-400"
                />
              </div>
              <div v-if="config.voice">
                <div class="flex items-center justify-between text-xs">
                  <span class="text-mist-500">音量</span>
                  <span class="text-electric-400">{{ Math.round(config.voice.volume * 100) }}%</span>
                </div>
                <input
                  v-model.number="config.voice.volume"
                  type="range"
                  min="0"
                  max="1"
                  step="0.05"
                  class="mt-2 w-full accent-electric-400"
                />
              </div>
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

          <!-- 主题 -->
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
                  class="mb-3 flex h-16 items-center justify-center rounded-md"
                  :style="{
                    background: `linear-gradient(135deg, ${t.primary} 0%, ${t.accent} 100%)`,
                  }"
                >
                  <span class="font-display text-xs font-semibold text-white drop-shadow">
                    {{ t.name }}
                  </span>
                </div>
                <div class="text-sm font-medium text-moon-50">{{ t.name }}</div>
                <p class="text-[11px] text-mist-500">{{ t.description }}</p>
              </button>
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
                <span class="text-mist-500">动画风格</span>
                <AppBadge tone="electric">
                  {{ ANIMATION_STYLES.find((s) => s.id === config.animationStyle)?.name }}
                </AppBadge>
              </div>
              <div class="flex items-center justify-between">
                <span class="text-mist-500">分辨率</span>
                <span class="text-moon-50">{{ config.resolution.toUpperCase() }}</span>
              </div>
              <div class="flex items-center justify-between">
                <span class="text-mist-500">画面比例</span>
                <span class="text-moon-50">{{ config.ratio }}</span>
              </div>
              <div class="flex items-center justify-between">
                <span class="text-mist-500">配音</span>
                <span class="text-moon-50">
                  {{ VOICES.find((v) => v.id === config.voice?.id)?.name ?? '无' }}
                </span>
              </div>
              <div class="flex items-center justify-between">
                <span class="text-mist-500">主题</span>
                <span class="text-moon-50">
                  {{ THEME_STYLES.find((t) => t.id === config.theme)?.name }}
                </span>
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
