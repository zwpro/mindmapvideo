<script setup lang="ts">
import { computed } from 'vue'
import { cn } from '@/lib/utils'

const props = withDefaults(
  defineProps<{
    interactive?: boolean
    padded?: boolean
    glow?: boolean
  }>(),
  {
    interactive: false,
    padded: true,
    glow: false,
  },
)

const classes = computed(() =>
  cn(
    'relative rounded-2xl border border-zinc-200 bg-white shadow-soft transition-all',
    props.padded && 'p-6',
    props.interactive && 'hover:border-electric-400/40 hover:-translate-y-0.5 cursor-pointer',
    props.glow && 'shadow-glow-sm',
  ),
)
</script>

<template>
  <div :class="classes">
    <slot />
  </div>
</template>
