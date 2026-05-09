<script setup lang="ts">
import { computed } from 'vue'
import { cn } from '@/lib/utils'

type Tone = 'neutral' | 'electric' | 'ember' | 'success' | 'warning' | 'danger'

const props = withDefaults(
  defineProps<{
    tone?: Tone
    dot?: boolean
  }>(),
  { tone: 'neutral', dot: false },
)

const wrap = computed(() =>
  cn(
    'inline-flex items-center gap-1.5 rounded-full px-2.5 py-1 text-xs font-medium border',
    {
      'bg-zinc-100 text-mist-400 border-zinc-200': props.tone === 'neutral',
      'bg-electric-400/10 text-electric-400 border-electric-400/30': props.tone === 'electric',
      'bg-ember-400/10 text-ember-400 border-ember-400/30': props.tone === 'ember',
      'bg-success/10 text-success border-success/30': props.tone === 'success',
      'bg-warning/10 text-warning border-warning/30': props.tone === 'warning',
      'bg-danger/10 text-danger border-danger/30': props.tone === 'danger',
    },
  ),
)

const dotClass = computed(() =>
  cn('h-1.5 w-1.5 rounded-full', {
    'bg-mist-400': props.tone === 'neutral',
    'bg-electric-400 animate-pulse': props.tone === 'electric',
    'bg-ember-400': props.tone === 'ember',
    'bg-success': props.tone === 'success',
    'bg-warning animate-pulse': props.tone === 'warning',
    'bg-danger': props.tone === 'danger',
  }),
)
</script>

<template>
  <span :class="wrap">
    <span v-if="dot" :class="dotClass" />
    <slot />
  </span>
</template>
