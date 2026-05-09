<script setup lang="ts">
import { computed, useAttrs } from 'vue'
import { cn } from '@/lib/utils'

defineOptions({ inheritAttrs: false })

const props = withDefaults(
  defineProps<{
    modelValue?: string
    placeholder?: string
    size?: 'sm' | 'md' | 'lg'
    glow?: boolean
    disabled?: boolean
  }>(),
  {
    size: 'md',
    glow: false,
    disabled: false,
    modelValue: '',
  },
)

const emit = defineEmits<{
  (e: 'update:modelValue', value: string): void
  (e: 'submit', value: string): void
}>()

const attrs = useAttrs()

const wrapperClass = computed(() =>
  cn(
    'group relative flex items-center gap-3 border bg-white transition-all',
    'focus-within:bg-white',
    {
      'h-10 rounded-md px-3 text-sm border-zinc-200 focus-within:border-electric-400/60': props.size === 'sm',
      'h-12 rounded-lg px-4 text-sm border-zinc-200 focus-within:border-electric-400/60': props.size === 'md',
      'h-16 rounded-xl px-6 text-base border-zinc-200 focus-within:border-electric-400/60 focus-within:shadow-glow':
        props.size === 'lg',
    },
    props.glow && 'shadow-glow-sm',
    props.disabled && 'opacity-60 cursor-not-allowed',
  ),
)

const onInput = (e: Event) => {
  emit('update:modelValue', (e.target as HTMLInputElement).value)
}

const onKey = (e: KeyboardEvent) => {
  if (e.key === 'Enter') {
    emit('submit', (e.target as HTMLInputElement).value)
  }
}
</script>

<template>
  <label :class="wrapperClass">
    <slot name="prefix" />
    <input
      v-bind="attrs"
      :value="modelValue"
      :placeholder="placeholder"
      :disabled="disabled"
      class="w-full bg-transparent text-moon-50 placeholder:text-mist-400 outline-none disabled:cursor-not-allowed"
      @input="onInput"
      @keydown="onKey"
    />
    <slot name="suffix" />
  </label>
</template>
