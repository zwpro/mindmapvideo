<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { Save, Trash2, Bell, BellOff, Database } from 'lucide-vue-next'
import PageShell from '@/components/layout/PageShell.vue'
import AppCard from '@/components/ui/AppCard.vue'
import AppButton from '@/components/ui/AppButton.vue'
import AppInput from '@/components/ui/AppInput.vue'
import AppBadge from '@/components/ui/AppBadge.vue'
import { useUserStore } from '@/stores/user'
import { useProjectStore } from '@/stores/projects'
import { useTaskStore } from '@/stores/tasks'
import { formatRelative } from '@/lib/format'

const userStore = useUserStore()
const projectStore = useProjectStore()
const taskStore = useTaskStore()

const nickname = ref(userStore.user.nickname)
const bio = ref(userStore.user.bio)
const saved = ref(false)

watch(
  () => userStore.user,
  (u) => {
    nickname.value = u.nickname
    bio.value = u.bio
  },
)

const save = () => {
  userStore.user.nickname = nickname.value.trim() || 'Admin'
  userStore.user.bio = bio.value
  saved.value = true
  setTimeout(() => (saved.value = false), 1500)
}

const stats = computed(() => ({
  projects: projectStore.projects.length,
  videos: Object.keys(taskStore.videos).length,
  notifications: userStore.notifications.length,
}))

const clearProjects = () => {
  if (!confirm('确定要清空所有项目数据吗？此操作不可撤销。')) return
  projectStore.projects = []
}

const clearNotifications = () => {
  userStore.notifications = []
}
</script>

<template>
  <PageShell>
    <div class="container-page py-10 max-w-4xl">
      <div class="mb-10">
        <AppBadge tone="ember" class="mb-3">个人中心</AppBadge>
        <h1 class="font-display text-3xl font-semibold text-moon-50">{{ userStore.user.nickname }}</h1>
        <p class="text-mist-400 mt-2">{{ userStore.user.bio }}</p>
      </div>

      <div class="grid gap-6 sm:grid-cols-3 mb-10">
        <AppCard class="p-5">
          <div class="text-xs text-mist-500 mb-2">项目数</div>
          <div class="font-display text-3xl font-semibold text-moon-50">{{ stats.projects }}</div>
        </AppCard>
        <AppCard class="p-5">
          <div class="text-xs text-mist-500 mb-2">已生成视频</div>
          <div class="font-display text-3xl font-semibold text-electric-400">{{ stats.videos }}</div>
        </AppCard>
        <AppCard class="p-5">
          <div class="text-xs text-mist-500 mb-2">通知数</div>
          <div class="font-display text-3xl font-semibold text-ember-400">{{ stats.notifications }}</div>
        </AppCard>
      </div>

      <AppCard class="p-6 mb-6">
        <h2 class="font-display text-lg font-semibold text-moon-50 mb-5">基本信息</h2>
        <div class="space-y-5">
          <div>
            <label class="block text-xs text-mist-500 mb-2">昵称</label>
            <AppInput v-model="nickname" placeholder="请输入昵称" />
          </div>
          <div>
            <label class="block text-xs text-mist-500 mb-2">简介</label>
            <textarea
              v-model="bio"
              rows="3"
              class="w-full bg-graphite-800 border border-graphite-700 rounded-xl px-4 py-2.5 text-sm text-moon-50 placeholder:text-mist-500 focus:outline-none focus:border-electric-400/40 transition resize-none"
              placeholder="一句话介绍自己"
            />
          </div>
          <div class="flex items-center gap-3">
            <AppButton variant="primary" @click="save">
              <Save class="h-4 w-4" />
              保存
            </AppButton>
            <span v-if="saved" class="text-xs text-electric-400">已保存</span>
          </div>
        </div>
      </AppCard>

      <AppCard class="p-6 mb-6">
        <div class="flex items-center justify-between mb-5">
          <div class="flex items-center gap-2">
            <Bell class="h-4 w-4 text-mist-400" />
            <h2 class="font-display text-lg font-semibold text-moon-50">通知</h2>
          </div>
          <div class="flex items-center gap-2">
            <button
              v-if="userStore.unreadCount > 0"
              class="text-xs text-mist-400 hover:text-electric-400 transition"
              @click="userStore.markAllRead()"
            >
              全部标记已读
            </button>
            <button
              v-if="userStore.notifications.length"
              class="text-xs text-mist-400 hover:text-danger transition"
              @click="clearNotifications"
            >
              清空
            </button>
          </div>
        </div>

        <div v-if="!userStore.notifications.length" class="py-10 text-center">
          <BellOff class="h-8 w-8 text-mist-500 mx-auto mb-3" />
          <p class="text-sm text-mist-500">暂无通知</p>
        </div>

        <ul v-else class="space-y-3">
          <li
            v-for="n in userStore.notifications"
            :key="n.id"
            class="flex items-start gap-3 p-3 rounded-lg border border-zinc-200 hover:border-electric-400/40 transition"
            :class="{ 'bg-indigo-50/60': !n.read }"
          >
            <span
              class="mt-1.5 h-2 w-2 rounded-full"
              :class="{
                'bg-electric-400 animate-pulse-ring': !n.read,
                'bg-mist-500': n.read,
              }"
            />
            <div class="flex-1 min-w-0">
              <div class="flex items-center justify-between gap-3">
                <p class="text-sm font-medium text-moon-50 truncate">{{ n.title }}</p>
                <span class="text-xs text-mist-500 shrink-0">{{ formatRelative(n.createdAt) }}</span>
              </div>
              <p class="mt-1 text-xs text-mist-400">{{ n.body }}</p>
            </div>
          </li>
        </ul>
      </AppCard>

      <AppCard class="p-6 border-danger/20">
        <div class="flex items-center gap-2 mb-3">
          <Database class="h-4 w-4 text-danger" />
          <h2 class="font-display text-lg font-semibold text-moon-50">数据管理</h2>
        </div>
        <p class="text-sm text-mist-400 mb-5">
          所有数据存储在浏览器本地。清空后不可恢复，请谨慎操作。
        </p>
        <AppButton variant="danger" @click="clearProjects">
          <Trash2 class="h-4 w-4" />
          清空所有项目
        </AppButton>
      </AppCard>
    </div>
  </PageShell>
</template>
