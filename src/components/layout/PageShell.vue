<script setup lang="ts">
import NavBar from './NavBar.vue'
import AppFooter from './AppFooter.vue'

withDefaults(
  defineProps<{
    fullHeight?: boolean
    hideFooter?: boolean
  }>(),
  { fullHeight: false, hideFooter: false },
)
</script>

<template>
  <div class="flex min-h-screen flex-col bg-ink-900">
    <NavBar />
    <main
      :class="[
        'flex-1 pt-16',
        fullHeight && 'flex flex-col',
      ]"
    >
      <slot />
    </main>
    <AppFooter v-if="!hideFooter" />
  </div>
</template>
