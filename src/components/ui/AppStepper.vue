<script setup lang="ts">
import { computed } from 'vue'
import { cn } from '@/lib/utils'
import { Check } from 'lucide-vue-next'

interface Step {
  key: string
  label: string
}

const props = withDefaults(
  defineProps<{
    steps: Step[]
    current: number
  }>(),
  { current: 0 },
)

const emit = defineEmits<{ (e: 'navigate', index: number): void }>()

const items = computed(() =>
  props.steps.map((s, i) => ({
    ...s,
    index: i,
    state:
      i < props.current
        ? ('done' as const)
        : i === props.current
          ? ('current' as const)
          : ('upcoming' as const),
  })),
)

const onClick = (i: number) => {
  if (i < props.current) emit('navigate', i)
}
</script>

<template>
  <ol class="flex w-full items-center gap-2">
    <li
      v-for="(item, i) in items"
      :key="item.key"
      class="flex flex-1 items-center"
    >
      <button
        type="button"
        :disabled="item.state !== 'done'"
        :class="
          cn(
            'group flex items-center gap-3 text-left transition-opacity',
            item.state === 'done' && 'cursor-pointer hover:opacity-90',
            item.state !== 'done' && 'cursor-default',
          )
        "
        @click="onClick(item.index)"
      >
        <span
          :class="
            cn(
              'flex h-9 w-9 shrink-0 items-center justify-center rounded-full border text-sm font-display font-semibold transition-all',
              item.state === 'done' && 'bg-electric-400 text-ink-900 border-electric-400',
              item.state === 'current' &&
                'bg-graphite-800 text-electric-400 border-electric-400 shadow-glow-sm animate-pulse-ring',
              item.state === 'upcoming' && 'bg-white text-mist-400 border-zinc-200',
            )
          "
        >
          <Check v-if="item.state === 'done'" class="h-4 w-4" />
          <span v-else>{{ i + 1 }}</span>
        </span>
        <div class="hidden flex-col md:flex">
          <span
            :class="
              cn(
                'text-sm font-medium',
                item.state === 'current' ? 'text-moon-50' : 'text-mist-400',
                item.state === 'done' && 'text-electric-400',
              )
            "
            >{{ item.label }}</span
          >
          <span class="text-[11px] text-mist-500">Step {{ i + 1 }}</span>
        </div>
      </button>
      <div
        v-if="i < steps.length - 1"
        :class="
          cn(
            'mx-3 h-px flex-1',
            item.state === 'done' ? 'bg-electric-400/60' : 'bg-zinc-200',
          )
        "
      />
    </li>
  </ol>
</template>
