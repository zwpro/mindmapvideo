<script setup lang="ts">
import { ref, onMounted, onUnmounted, computed } from 'vue'
import { useRoute, RouterLink } from 'vue-router'
import { Bell } from 'lucide-vue-next'
import { useUserStore } from '@/stores/user'
import { cn } from '@/lib/utils'
import logoUrl from '@/assets/logo.png'

const scrolled = ref(false)
const onScroll = () => {
  scrolled.value = window.scrollY > 16
}
onMounted(() => {
  window.addEventListener('scroll', onScroll, { passive: true })
  onScroll()
})
onUnmounted(() => window.removeEventListener('scroll', onScroll))

const route = useRoute()
const user = useUserStore()

const links = [
  { to: '/', label: '首页' },
  { to: '/dashboard', label: '工作台' },
]

const headerClass = computed(() =>
  cn(
    'fixed inset-x-0 top-0 z-40 transition-all duration-300',
    scrolled.value
      ? 'border-b border-zinc-200 bg-white/85 backdrop-blur-xl shadow-soft'
      : 'border-b border-transparent bg-transparent',
  ),
)
</script>

<template>
  <header :class="headerClass">
    <div
      class="mx-auto flex h-16 w-full max-w-[1280px] items-center justify-between px-6 lg:px-10"
    >
      <RouterLink
        to="/"
        class="flex items-center gap-2 text-moon-50 hover:text-electric-400 transition-colors"
      >
        <img
          :src="logoUrl"
          alt="MindMapVideo"
          class="h-9 w-9 rounded-md object-contain"
        />
        <span class="font-display text-lg font-semibold tracking-tight"
          >MindMap<span class="text-electric-400">Video</span></span
        >
      </RouterLink>

      <nav class="hidden items-center gap-1 md:flex">
        <RouterLink
          v-for="link in links"
          :key="link.to"
          :to="link.to"
          :class="
            cn(
              'rounded-md px-3 py-1.5 text-sm transition-colors',
              route.path === link.to
                ? 'text-electric-400'
                : 'text-mist-400 hover:text-moon-50',
            )
          "
          >{{ link.label }}</RouterLink
        >
      </nav>

      <div class="flex items-center gap-3">
        <RouterLink
          to="/dashboard"
          class="hidden h-9 items-center rounded-md border border-zinc-300 bg-white px-4 text-sm font-medium text-moon-50 transition-all hover:border-electric-400/60 hover:text-electric-400 md:inline-flex"
          >进入工作台</RouterLink
        >
        <RouterLink
          to="/profile"
          class="relative grid h-9 w-9 place-items-center rounded-full border border-zinc-300 bg-white transition-all hover:border-electric-400/40"
          aria-label="用户中心"
        >
          <Bell class="h-4 w-4 text-mist-400" />
          <span
            v-if="user.unreadCount > 0"
            class="absolute -right-0.5 -top-0.5 grid h-4 min-w-4 place-items-center rounded-full bg-ember-400 px-1 text-[10px] font-bold text-ink-900"
            >{{ user.unreadCount }}</span
          >
        </RouterLink>
        <RouterLink
          to="/profile"
          class="grid h-9 w-9 overflow-hidden rounded-full border border-electric-400/30"
        >
          <img
            :src="user.user.avatarUrl"
            :alt="user.user.nickname"
            class="h-full w-full object-cover"
          />
        </RouterLink>
      </div>
    </div>
  </header>
</template>
