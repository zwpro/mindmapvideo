<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ArrowLeft, Download, Share2, Sparkles, RotateCcw, Film } from 'lucide-vue-next'
import PageShell from '@/components/layout/PageShell.vue'
import AppButton from '@/components/ui/AppButton.vue'
import AppCard from '@/components/ui/AppCard.vue'
import AppBadge from '@/components/ui/AppBadge.vue'
import { useTaskStore } from '@/stores/tasks'
import { useProjectStore } from '@/stores/projects'
import { formatFileSize, formatDuration, formatRelative } from '@/lib/format'

const props = defineProps<{ videoId: string }>()
const router = useRouter()
const taskStore = useTaskStore()
const projectStore = useProjectStore()

const video = computed(() => taskStore.videoById(props.videoId))
const project = computed(() =>
  video.value ? projectStore.byId(video.value.projectId) : null,
)

const loading = ref(true)
const loadError = ref<string | null>(null)

onMounted(async () => {
  loading.value = true
  loadError.value = null
  try {
    const detail = await taskStore.fetchVideo(props.videoId)
    if (!projectStore.byId(detail.projectId)) {
      await projectStore.fetchOne(detail.projectId).catch(() => undefined)
    }
  } catch (err) {
    loadError.value = err instanceof Error ? err.message : '加载视频失败'
  } finally {
    loading.value = false
  }
})

const copied = ref(false)
const share = async () => {
  try {
    await navigator.clipboard.writeText(window.location.href)
    copied.value = true
    setTimeout(() => (copied.value = false), 1500)
  } catch {
    /* noop */
  }
}

const download = () => {
  if (!video.value) return
  const a = document.createElement('a')
  a.href = video.value.url
  a.download = `${project.value?.topic || 'mindmap'}.mp4`
  a.click()
}

const regenerate = () => {
  if (!project.value) return
  router.push({ name: 'config', params: { projectId: project.value.id } })
}
</script>

<template>
  <PageShell>
    <div class="container-page py-10">
      <button
        class="inline-flex items-center gap-1.5 text-sm text-mist-400 hover:text-electric-400 mb-6 transition"
        @click="router.push({ name: 'dashboard' })"
      >
        <ArrowLeft class="h-4 w-4" />
        返回工作台
      </button>

      <div v-if="loading" class="text-center py-24 text-mist-400 text-sm">
        正在加载视频…
      </div>

      <div v-else-if="!video" class="text-center py-24">
        <Film class="h-12 w-12 text-mist-500 mx-auto mb-4" />
        <p class="text-mist-400">{{ loadError || '视频不存在或已被删除' }}</p>
        <AppButton class="mt-6" variant="secondary" @click="router.push({ name: 'dashboard' })">
          返回工作台
        </AppButton>
      </div>

      <div v-else class="grid grid-cols-1 lg:grid-cols-[1fr_360px] gap-8">
        <div>
          <div class="flex items-center gap-3 mb-4">
            <AppBadge tone="success">
              <Sparkles class="h-3 w-3" />
              已完成
            </AppBadge>
            <span class="text-xs text-mist-500">{{ formatRelative(video.createdAt) }}</span>
          </div>
          <h1 class="font-display text-3xl font-semibold text-moon-50 mb-6">
            {{ project?.topic || '未命名项目' }}
          </h1>

          <AppCard :padded="false" class="!rounded-lg overflow-hidden">
            <div class="aspect-video bg-zinc-950 relative">
              <video
                :src="video.url"
                :poster="video.thumbnailUrl"
                controls
                class="w-full h-full object-contain"
              />
            </div>
          </AppCard>

          <div class="mt-6 flex flex-wrap gap-3">
            <AppButton variant="primary" @click="download">
              <Download class="h-4 w-4" />
              下载视频
            </AppButton>
            <AppButton variant="secondary" @click="share">
              <Share2 class="h-4 w-4" />
              {{ copied ? '链接已复制' : '复制链接' }}
            </AppButton>
            <AppButton variant="ghost" @click="regenerate">
              <RotateCcw class="h-4 w-4" />
              重新生成
            </AppButton>
          </div>
        </div>

        <div class="space-y-4">
          <AppCard class="p-5">
            <h3 class="font-display text-sm font-semibold text-moon-50 mb-4">视频信息</h3>
            <dl class="space-y-3 text-sm">
              <div class="flex justify-between">
                <dt class="text-mist-500">时长</dt>
                <dd class="text-moon-50 font-mono">{{ formatDuration(video.duration) }}</dd>
              </div>
              <div class="flex justify-between">
                <dt class="text-mist-500">分辨率</dt>
                <dd class="text-moon-50">{{ video.resolution }}</dd>
              </div>
              <div class="flex justify-between">
                <dt class="text-mist-500">比例</dt>
                <dd class="text-moon-50">{{ video.ratio }}</dd>
              </div>
              <div class="flex justify-between">
                <dt class="text-mist-500">大小</dt>
                <dd class="text-moon-50">{{ formatFileSize(video.fileSize) }}</dd>
              </div>
              <div class="flex justify-between">
                <dt class="text-mist-500">生成时间</dt>
                <dd class="text-moon-50">{{ formatRelative(video.createdAt) }}</dd>
              </div>
            </dl>
          </AppCard>

          <AppCard v-if="project" class="p-5">
            <h3 class="font-display text-sm font-semibold text-moon-50 mb-4">主题</h3>
            <p class="text-sm text-mist-400 leading-relaxed">{{ project.topic }}</p>
          </AppCard>
        </div>
      </div>
    </div>
  </PageShell>
</template>
