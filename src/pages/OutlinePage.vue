<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { nanoid } from 'nanoid'
import {
  ArrowLeft,
  ArrowRight,
  RefreshCw,
  Plus,
  Trash2,
  ArrowUp,
  ArrowDown,
  Save,
  FileText,
} from 'lucide-vue-next'
import PageShell from '@/components/layout/PageShell.vue'
import AppButton from '@/components/ui/AppButton.vue'
import AppCard from '@/components/ui/AppCard.vue'
import AppInput from '@/components/ui/AppInput.vue'
import AppStepper from '@/components/ui/AppStepper.vue'
import { useProjectStore } from '@/stores/projects'
import { sceneApi } from '@/lib/api'
import type { Scene } from '@/types'

const route = useRoute()
const router = useRouter()
const projects = useProjectStore()

const projectId = computed(() => route.params.projectId as string)
const project = computed(() => projects.byId(projectId.value))

const scenes = ref<Scene[]>([])
const streaming = ref(false)
const selectedId = ref<string | null>(null)

const STEPS = [
  { key: 'outline', label: '大纲生成' },
  { key: 'config', label: '视频配置' },
  { key: 'progress', label: '生成视频' },
  { key: 'preview', label: '预览导出' },
]

const selectedIndex = computed(() =>
  scenes.value.findIndex((s) => s.id === selectedId.value),
)
const selectedScene = computed<Scene | null>(() =>
  selectedIndex.value >= 0 ? scenes.value[selectedIndex.value] : null,
)

const totalWords = computed(() =>
  scenes.value.reduce((sum, s) => sum + s.content.length, 0),
)

const estimatedDuration = computed(() => {
  const seconds = Math.max(20, Math.round(totalWords.value / 4))
  const m = Math.floor(seconds / 60)
  const s = seconds % 60
  return m > 0 ? `${m} 分 ${s} 秒` : `${s} 秒`
})

const reindex = () => {
  scenes.value.forEach((s, i) => {
    s.index = i
  })
}

const persist = () => {
  if (!project.value) return
  reindex()
  const snapshot = JSON.parse(JSON.stringify(scenes.value)) as Scene[]
  if (typeof projects.setScenes === 'function') {
    projects.setScenes(projectId.value, snapshot)
  } else {
    projects.update(projectId.value, { scenes: snapshot })
  }
}

const startStream = async () => {
  if (!project.value) return
  scenes.value = []
  streaming.value = true
  selectedId.value = null
  try {
    const list = await sceneApi.generateScenes(project.value.topic)
    scenes.value = list.map((s) => ({ ...s }))
    selectedId.value = scenes.value[0]?.id ?? null
    reindex()
    persist()
  } catch (err) {
    console.error('[OutlinePage] generateScenes failed', err)
  } finally {
    streaming.value = false
  }
}

const regenerate = () => {
  if (streaming.value) return
  startStream()
}

const onSelect = (id: string) => {
  selectedId.value = id
}

const addScene = () => {
  const newScene: Scene = {
    id: `s-${nanoid(6)}`,
    index: scenes.value.length,
    title: '新增分镜',
    content: '在右侧编辑这一页要讲的内容…',
  }
  const insertAt =
    selectedIndex.value >= 0 ? selectedIndex.value + 1 : scenes.value.length
  scenes.value.splice(insertAt, 0, newScene)
  selectedId.value = newScene.id
  persist()
}

const removeScene = (id: string) => {
  const i = scenes.value.findIndex((s) => s.id === id)
  if (i < 0) return
  scenes.value.splice(i, 1)
  if (selectedId.value === id) {
    selectedId.value =
      scenes.value[i]?.id ?? scenes.value[i - 1]?.id ?? null
  }
  persist()
}

const moveScene = (id: string, direction: -1 | 1) => {
  const i = scenes.value.findIndex((s) => s.id === id)
  if (i < 0) return
  const j = i + direction
  if (j < 0 || j >= scenes.value.length) return
  const [item] = scenes.value.splice(i, 1)
  scenes.value.splice(j, 0, item)
  persist()
}

const onTitleInput = (value: string) => {
  if (!selectedScene.value) return
  selectedScene.value.title = value
}
const onContentInput = (e: Event) => {
  if (!selectedScene.value) return
  const target = e.target as HTMLTextAreaElement
  selectedScene.value.content = target.value
}

let saveTimer: ReturnType<typeof setTimeout> | null = null
watch(
  scenes,
  () => {
    if (streaming.value) return
    if (saveTimer) clearTimeout(saveTimer)
    saveTimer = setTimeout(persist, 600)
  },
  { deep: true },
)

const goBack = () => router.push({ name: 'home' })
const goNext = () => {
  if (!project.value || streaming.value || !scenes.value.length) return
  persist()
  router.push({ name: 'config', params: { projectId: projectId.value } })
}

onMounted(async () => {
  if (!project.value) {
    try {
      await projects.fetchOne(projectId.value)
    } catch {
      router.replace({ name: 'home' })
      return
    }
  }
  if (!project.value) {
    router.replace({ name: 'home' })
    return
  }
  if (project.value.scenes && project.value.scenes.length) {
    scenes.value = JSON.parse(JSON.stringify(project.value.scenes))
    selectedId.value = scenes.value[0]?.id ?? null
  } else {
    startStream()
  }
})

onUnmounted(() => {
  if (saveTimer) clearTimeout(saveTimer)
})
</script>

<template>
  <PageShell full-height>
    <div class="container-page flex h-full flex-col gap-6 py-8">
      <!-- HEADER -->
      <div class="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
        <div class="space-y-2">
          <button
            class="inline-flex items-center gap-1 text-xs uppercase tracking-[0.3em] text-mist-400 transition hover:text-electric-400"
            @click="goBack"
          >
            <ArrowLeft class="h-3.5 w-3.5" /> 返回首页
          </button>
          <h1 class="font-display text-3xl text-moon-50">分镜大纲</h1>
          <p class="text-sm text-mist-400">
            主题：<span class="text-moon-50">{{ project?.topic }}</span> · 共
            <span class="text-electric-400">{{ scenes.length }}</span> 页 · 预估时长 {{ estimatedDuration }}
          </p>
        </div>
        <div class="flex flex-wrap items-center gap-3">
          <AppStepper :steps="STEPS" :current="0" />
          <div class="flex items-center gap-2">
            <AppButton
              variant="ghost"
              size="sm"
              :disabled="streaming"
              @click="regenerate"
            >
              <RefreshCw class="h-4 w-4" /> 重新生成
            </AppButton>
            <AppButton
              variant="primary"
              size="sm"
              :disabled="streaming || !scenes.length"
              @click="goNext"
            >
              {{ streaming ? '生成中…' : '下一步 · 视频配置' }}
              <ArrowRight v-if="!streaming" class="h-4 w-4" />
            </AppButton>
          </div>
        </div>
      </div>

      <!-- WORKSPACE -->
      <div class="grid flex-1 grid-cols-1 gap-6 lg:grid-cols-[360px_1fr]">
        <!-- 分镜列表 -->
        <AppCard padded class="flex flex-col">
          <div class="flex items-center justify-between">
            <div>
              <p class="text-xs uppercase tracking-[0.3em] text-mist-400">分镜列表</p>
              <p class="mt-1 text-sm text-moon-50">点击切换 · 拖拽顺序由 ↑↓ 控制</p>
            </div>
            <AppButton
              variant="ghost"
              size="sm"
              :disabled="streaming"
              @click="addScene"
            >
              <Plus class="h-4 w-4" /> 添加
            </AppButton>
          </div>

          <div class="mt-4 flex-1 space-y-2 overflow-y-auto pr-1">
            <div
              v-for="(scene, idx) in scenes"
              :key="scene.id"
              :class="[
                'group cursor-pointer rounded-xl border p-3 transition-all',
                selectedId === scene.id
                  ? 'border-electric-400 bg-indigo-50 shadow-soft'
                  : 'border-zinc-200 bg-white hover:border-electric-400/40 hover:bg-zinc-50',
              ]"
              @click="onSelect(scene.id)"
            >
              <div class="flex items-start gap-3">
                <span
                  :class="[
                    'mt-0.5 flex h-6 w-6 shrink-0 items-center justify-center rounded-full text-[11px] font-display',
                    selectedId === scene.id
                      ? 'bg-electric-400 text-white'
                      : 'bg-zinc-100 text-mist-400',
                  ]"
                >
                  {{ idx + 1 }}
                </span>
                <div class="min-w-0 flex-1">
                  <p class="truncate text-sm text-moon-50">{{ scene.title || '未命名分镜' }}</p>
                  <p class="mt-1 line-clamp-2 text-xs text-mist-400">
                    {{ scene.content || '暂无内容…' }}
                  </p>
                </div>
              </div>
              <div
                class="mt-2 flex items-center justify-end gap-1 opacity-0 transition group-hover:opacity-100"
                :class="{ 'opacity-100': selectedId === scene.id }"
              >
                <button
                  class="rounded-md p-1 text-mist-400 transition hover:bg-zinc-100 hover:text-moon-50 disabled:opacity-40"
                  :disabled="idx === 0"
                  title="上移"
                  @click.stop="moveScene(scene.id, -1)"
                >
                  <ArrowUp class="h-3.5 w-3.5" />
                </button>
                <button
                  class="rounded-md p-1 text-mist-400 transition hover:bg-zinc-100 hover:text-moon-50 disabled:opacity-40"
                  :disabled="idx === scenes.length - 1"
                  title="下移"
                  @click.stop="moveScene(scene.id, 1)"
                >
                  <ArrowDown class="h-3.5 w-3.5" />
                </button>
                <button
                  class="rounded-md p-1 text-mist-400 transition hover:bg-rose-50 hover:text-rose-500 disabled:opacity-40"
                  :disabled="scenes.length <= 1"
                  title="删除"
                  @click.stop="removeScene(scene.id)"
                >
                  <Trash2 class="h-3.5 w-3.5" />
                </button>
              </div>
            </div>

            <div
              v-if="streaming"
              class="rounded-xl border border-dashed border-electric-400/40 bg-indigo-50/50 p-3 text-center text-xs text-electric-400"
            >
              正在生成分镜…
            </div>

            <div
              v-if="!streaming && !scenes.length"
              class="rounded-xl border border-dashed border-zinc-200 p-6 text-center text-xs text-mist-400"
            >
              暂无分镜，点击「重新生成」或「添加」开始创建。
            </div>
          </div>
        </AppCard>

        <!-- 编辑面板 -->
        <AppCard padded class="flex flex-col">
          <template v-if="selectedScene">
            <div class="flex items-start justify-between gap-4">
              <div>
                <p class="text-xs uppercase tracking-[0.3em] text-mist-400">
                  第 {{ selectedIndex + 1 }} / {{ scenes.length }} 页
                </p>
                <p class="mt-1 text-sm text-mist-400">分镜内容会用于视频中的旁白与字幕</p>
              </div>
              <div class="flex items-center gap-2 text-xs text-mist-400">
                <Save class="h-3.5 w-3.5" />
                <span>自动保存</span>
              </div>
            </div>

            <div class="mt-5 space-y-2">
              <label class="text-xs uppercase tracking-[0.3em] text-mist-400">分镜标题</label>
              <AppInput
                :model-value="selectedScene.title"
                placeholder="给这一页起个标题"
                size="md"
                class="w-full"
                @update:model-value="onTitleInput"
              />
            </div>

            <div class="mt-5 flex flex-1 flex-col">
              <div class="flex items-center justify-between">
                <label class="text-xs uppercase tracking-[0.3em] text-mist-400">分镜内容</label>
                <span class="text-xs text-mist-400">
                  <FileText class="mr-1 inline h-3 w-3" />
                  {{ selectedScene.content.length }} 字
                </span>
              </div>
              <textarea
                :value="selectedScene.content"
                placeholder="这一页要讲的内容（建议 60-200 字）"
                class="mt-2 min-h-[260px] flex-1 resize-none rounded-xl border border-zinc-200 bg-white p-4 text-sm text-moon-50 placeholder:text-mist-400/60 focus:border-electric-400 focus:outline-none focus:ring-2 focus:ring-electric-400/20"
                @input="onContentInput"
              ></textarea>
            </div>

            <div class="mt-5 grid grid-cols-3 gap-3">
              <div class="rounded-xl border border-zinc-200 bg-zinc-50 p-3">
                <p class="text-xs text-mist-400">页码</p>
                <p class="mt-1 font-display text-lg text-moon-50">
                  {{ selectedIndex + 1 }} / {{ scenes.length }}
                </p>
              </div>
              <div class="rounded-xl border border-zinc-200 bg-zinc-50 p-3">
                <p class="text-xs text-mist-400">本页字数</p>
                <p class="mt-1 font-display text-lg text-moon-50">
                  {{ selectedScene.content.length }}
                </p>
              </div>
              <div class="rounded-xl border border-zinc-200 bg-zinc-50 p-3">
                <p class="text-xs text-mist-400">全篇总字数</p>
                <p class="mt-1 font-display text-lg text-moon-50">{{ totalWords }}</p>
              </div>
            </div>
          </template>

          <div
            v-else
            class="flex flex-1 items-center justify-center text-sm text-mist-400"
          >
            从左侧选择一页分镜开始编辑
          </div>
        </AppCard>
      </div>
    </div>
  </PageShell>
</template>
