<script setup lang="ts">
import { onMounted } from 'vue'
import { useUserStore } from '@/stores/user'

const user = useUserStore()

onMounted(() => {
  user.fetchMe().catch(() => undefined)
})
</script>

<template>
  <router-view />
</template>
