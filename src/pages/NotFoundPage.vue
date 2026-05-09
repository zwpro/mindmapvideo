<script setup lang="ts">
import { useRouter } from 'vue-router'
import { Home, Compass } from 'lucide-vue-next'
import PageShell from '@/components/layout/PageShell.vue'
import AppButton from '@/components/ui/AppButton.vue'

const router = useRouter()
</script>

<template>
  <PageShell>
    <div class="container-page py-24 text-center">
      <div class="font-display text-[120px] leading-none font-bold bg-gradient-to-br from-electric-400 to-ember-400 bg-clip-text text-transparent">
        404
      </div>
      <h1 class="font-display text-2xl font-semibold text-moon-50 mt-4">页面走失了</h1>
      <p class="text-mist-400 mt-3 max-w-md mx-auto">
        你访问的页面不存在，可能已被移除或链接有误。
      </p>

      <div class="mt-10 flex flex-wrap justify-center gap-3">
        <AppButton variant="primary" @click="router.push({ name: 'home' })">
          <Home class="h-4 w-4" />
          返回首页
        </AppButton>
        <AppButton variant="secondary" @click="router.push({ name: 'dashboard' })">
          <Compass class="h-4 w-4" />
          进入工作台
        </AppButton>
      </div>
    </div>
  </PageShell>
</template>
