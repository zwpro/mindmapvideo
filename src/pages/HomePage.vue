<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import {
  Sparkles,
  ArrowRight,
  Brain,
  Wand2,
  Clapperboard,
  Lightbulb,
  Layers,
  Rocket,
  PlayCircle,
} from 'lucide-vue-next'
import PageShell from '@/components/layout/PageShell.vue'
import AppButton from '@/components/ui/AppButton.vue'
import AppCard from '@/components/ui/AppCard.vue'
import AppBadge from '@/components/ui/AppBadge.vue'
import AppInput from '@/components/ui/AppInput.vue'
import { useCreateProject } from '@/composables/useCreateProject'
import { POPULAR_TOPICS } from '@/lib/constants'

const router = useRouter()
const topic = ref('')
const submitting = ref(false)
const { createAndGo } = useCreateProject()

const submit = () => {
  const value = topic.value.trim()
  if (!value || submitting.value) return
  submitting.value = true
  try {
    createAndGo(value)
  } finally {
    submitting.value = false
  }
}

const useSuggestion = (s: string) => {
  topic.value = s
}

const openCase = (id: string) => {
  router.push({ name: 'preview', params: { videoId: id } })
}

const steps = [
  {
    icon: Brain,
    title: '输入主题',
    desc: '一句话写下你想讲的内容，AI 会在数秒内拆解成分镜大纲。',
  },
  {
    icon: Wand2,
    title: '编辑分镜',
    desc: '在可视化编辑器中确认、调整每一幕分镜脚本，所见即所得。',
  },
  {
    icon: Clapperboard,
    title: '生成视频',
    desc: '一键提交到后端渲染管线，实时跟踪进度并预览成片。',
  },
]

const cases = [
  {
    title: '成大事前，先研究自己',
    duration: '01:13',
    nodes: 7,
    id: 'vqdEXpZnp0IC',
    cover: 'https://mindmap-api.vuseai.com/media/thumbnails/vqdEXpZnp0IC.jpg',
  },
  {
    title: '未来已来：AI 正在改变一切',
    duration: '00:59',
    nodes: 6,
    id: '8n8QpAmMR3Rx',
    cover: 'https://mindmap-api.vuseai.com/media/thumbnails/8n8QpAmMR3Rx.jpg',
  },
  {
    title: '福祸相依，否极泰来',
    duration: '01:10',
    nodes: 6,
    id: 'UPpedtL-ujgM',
    cover: 'https://mindmap-api.vuseai.com/media/thumbnails/UPpedtL-ujgM.jpg',
  },
]

const features = [
  {
    icon: Lightbulb,
    title: '智能拆解',
    desc: '输入任意主题，AI 自动生成结构清晰的分镜大纲，覆盖教学、科普、讲解等多种场景。',
  },
  {
    icon: Layers,
    title: '可视化编辑',
    desc: '逐镜编辑文案、旁白与画面描述，支持增删、排序与实时预览，所改即所见。',
  },
  {
    icon: Rocket,
    title: '一键出片',
    desc: '选择模板与配音风格后一键提交，全流程跟踪渲染进度，分镜自动合成完整视频。',
  },
]
</script>

<template>
  <PageShell>
    <section class="relative overflow-hidden">
      <div class="absolute inset-0 bg-hero-glow pointer-events-none" />
      <div class="absolute inset-0 grid-bg opacity-40 pointer-events-none" />

      <div class="container-page relative pt-12 pb-14 lg:pt-16 lg:pb-20">
        <div class="mx-auto max-w-3xl text-center animate-fade-up">
          <AppBadge tone="electric" class="mb-6 inline-flex items-center gap-1.5">
            <Sparkles class="h-3.5 w-3.5" />
            AI 驱动 · 思维导图视频生成
          </AppBadge>

          <h1 class="font-display text-4xl sm:text-5xl lg:text-6xl font-semibold tracking-tight text-moon-50">
            一句话，
            <span class="bg-gradient-to-r from-electric-400 to-ember-400 bg-clip-text text-transparent">
              生成思维导图视频
            </span>
          </h1>

          <p class="mt-6 text-lg text-mist-400 leading-relaxed">
            输入主题 → AI 生成分镜大纲 → 你确认与编辑 → 一键渲染成片。<br />
            无需剪辑技能，3 步创建结构清晰、节奏流畅的知识短视频。
          </p>

          <form
            class="mt-10 flex flex-col sm:flex-row items-center justify-center gap-3 w-full max-w-xl mx-auto"
            @submit.prevent="submit"
          >
            <AppInput
              v-model="topic"
              placeholder="例如：用三分钟讲清楚相对论"
              class="flex-1 min-w-0"
              size="lg"
            />
            <AppButton
              type="submit"
              variant="primary"
              size="lg"
              class="w-full sm:w-auto shrink-0"
              :loading="submitting"
              :disabled="!topic.trim()"
            >
              开始生成
              <ArrowRight class="h-4 w-4" />
            </AppButton>
          </form>

          <div class="mt-5 flex flex-wrap justify-center gap-2">
            <button
              v-for="s in POPULAR_TOPICS"
              :key="s"
              type="button"
              class="text-xs text-mist-400 hover:text-electric-400 px-3 py-1.5 rounded-full border border-graphite-700 hover:border-electric-400/40 transition"
              @click="useSuggestion(s)"
            >
              {{ s }}
            </button>
          </div>
        </div>
      </div>
    </section>

    <section class="container-page py-10 lg:py-14">
      <div class="grid gap-6 md:grid-cols-3">
        <AppCard
          v-for="(step, idx) in steps"
          :key="step.title"
          class="relative p-7 hover:border-electric-400/40 transition group"
        >
          <div class="absolute -top-3 -right-3 h-9 w-9 rounded-full bg-electric-400 text-ink-900 font-display font-semibold flex items-center justify-center shadow-glow-sm">
            {{ idx + 1 }}
          </div>
          <component
            :is="step.icon"
            class="h-9 w-9 text-electric-400 mb-4 group-hover:scale-110 transition"
          />
          <h3 class="font-display text-xl font-semibold text-moon-50 mb-2">
            {{ step.title }}
          </h3>
          <p class="text-sm text-mist-400 leading-relaxed">{{ step.desc }}</p>
        </AppCard>
      </div>
    </section>

    <section class="container-page py-10 lg:py-14">
      <div class="flex flex-col md:flex-row md:items-end md:justify-between gap-6 mb-8">
        <div>
          <AppBadge tone="ember" class="mb-3">案例展示</AppBadge>
          <h2 class="font-display text-h2 font-semibold text-moon-50">看看别人是怎么用的</h2>
        </div>
        <p class="text-mist-400 max-w-md">
          从科普讲解到面试备考，分镜视频的创作场景没有边界。
        </p>
      </div>

      <div class="grid gap-6 md:grid-cols-3">
        <AppCard
          v-for="c in cases"
          :key="c.title"
          :padded="false"
          class="overflow-hidden group cursor-pointer hover:-translate-y-1 transition"
          @click="openCase(c.id)"
        >
          <div
            class="relative h-44 bg-cover bg-center border-b border-graphite-700"
            :style="{ backgroundImage: `url(${c.cover})` }"
          >
            <div class="absolute inset-0 bg-zinc-900/30 group-hover:bg-zinc-900/10 transition" />
            <div class="absolute inset-0 flex items-center justify-center">
              <PlayCircle
                class="h-14 w-14 text-white/80 group-hover:text-electric-400 group-hover:scale-110 transition drop-shadow-lg"
              />
            </div>
            <span class="absolute bottom-3 right-3 text-xs font-mono text-white bg-zinc-900/75 px-2 py-1 rounded">
              {{ c.duration }}
            </span>
          </div>
          <div class="p-5">
            <h3 class="font-display text-lg font-semibold text-moon-50">{{ c.title }}</h3>
            <p class="mt-2 text-xs text-mist-400">{{ c.nodes }} 个分镜</p>
          </div>
        </AppCard>
      </div>
    </section>

    <section class="container-page py-10 lg:py-14">
      <div class="grid gap-6 md:grid-cols-3">
        <div
          v-for="f in features"
          :key="f.title"
          class="p-7 rounded-2xl border border-graphite-700 bg-white shadow-soft"
        >
          <component :is="f.icon" class="h-7 w-7 text-ember-400 mb-4" />
          <h3 class="font-display text-lg font-semibold text-moon-50 mb-2">
            {{ f.title }}
          </h3>
          <p class="text-sm text-mist-400 leading-relaxed">{{ f.desc }}</p>
        </div>
      </div>
    </section>

    <section class="container-page pt-10 pb-16 lg:pt-14 lg:pb-20">
      <div class="rounded-3xl border border-electric-400/20 bg-gradient-to-br from-indigo-50 via-white to-orange-50 p-10 lg:p-14 text-center relative overflow-hidden shadow-soft">
        <div class="absolute inset-0 bg-hero-glow opacity-60 pointer-events-none" />
        <div class="relative">
          <h2 class="font-display text-h2 font-semibold text-moon-50 mb-4">
            准备好把你的想法变成视频了吗？
          </h2>
          <p class="text-mist-400 mb-8 max-w-xl mx-auto">
            不用打开剪辑软件，不用手写分镜脚本。只需输入主题，剩下的交给 AI。
          </p>
          <AppButton variant="primary" size="lg" @click="router.push({ name: 'dashboard' })">
            进入工作台
            <ArrowRight class="h-4 w-4" />
          </AppButton>
        </div>
      </div>
    </section>
  </PageShell>
</template>
