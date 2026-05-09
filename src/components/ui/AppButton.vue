<script setup lang="ts">
import { computed } from 'vue'
import { cn } from '@/lib/utils'

type Variant = 'primary' | 'secondary' | 'ghost' | 'danger' | 'ember'
type Size = 'sm' | 'md' | 'lg'

const props = withDefaults(
  defineProps<{
    variant?: Variant
    size?: Size
    type?: 'button' | 'submit' | 'reset'
    disabled?: boolean
    loading?: boolean
    block?: boolean
  }>(),
  {
    variant: 'primary',
    size: 'md',
    type: 'button',
    disabled: false,
    loading: false,
    block: false,
  },
)

const classes = computed(() =>
  cn(
    'inline-flex items-center justify-center gap-2 font-medium tracking-wide',
    'transition-all duration-200 select-none',
    'border focus:outline-none focus-visible:ring-2 focus-visible:ring-electric-400/60',
    'disabled:opacity-50 disabled:cursor-not-allowed',
    {
      'h-9 px-3 text-sm rounded-md': props.size === 'sm',
      'h-11 px-5 text-sm rounded-md': props.size === 'md',
      'h-14 px-7 text-base rounded-lg': props.size === 'lg',
    },
    {
      'bg-electric-400 text-ink-900 border-electric-400 hover:scale-[1.02] hover:shadow-glow':
        props.variant === 'primary',
      'bg-white text-moon-50 border-zinc-300 hover:border-electric-400/60 hover:text-electric-400':
        props.variant === 'secondary',
      'bg-transparent text-mist-400 border-transparent hover:text-moon-50 hover:bg-zinc-100':
        props.variant === 'ghost',
      'bg-danger/15 text-danger border-danger/40 hover:bg-danger/25':
        props.variant === 'danger',
      'bg-ember-400 text-ink-900 border-ember-400 hover:scale-[1.02] hover:shadow-ember':
        props.variant === 'ember',
    },
    props.block && 'w-full',
  ),
)
</script>

<template>
  <button :type="type" :disabled="disabled || loading" :class="classes">
    <span
      v-if="loading"
      class="inline-block h-4 w-4 animate-spin rounded-full border-2 border-current border-t-transparent"
    />
    <slot />
  </button>
</template>
