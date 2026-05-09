<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import type { OutlineNode } from '@/types'
import { layoutMindmap, type LaidOutNode } from '@/lib/mindmapLayout'
import { cn } from '@/lib/utils'

const props = withDefaults(
  defineProps<{
    root: OutlineNode | null
    selectedId?: string | null
    streaming?: boolean
    readonly?: boolean
  }>(),
  {
    selectedId: null,
    streaming: false,
    readonly: false,
  },
)

const emit = defineEmits<{
  (e: 'select', id: string): void
  (e: 'addChild', id: string): void
  (e: 'edit', id: string): void
}>()

const layout = computed(() => layoutMindmap(props.root))

const scale = ref(1)
const offset = ref({ x: 24, y: 24 })

const dragState = ref<{ x: number; y: number; ox: number; oy: number } | null>(
  null,
)

const onWheel = (e: WheelEvent) => {
  if (!e.ctrlKey && !e.metaKey) return
  e.preventDefault()
  const delta = e.deltaY > 0 ? -0.08 : 0.08
  scale.value = Math.max(0.5, Math.min(1.6, scale.value + delta))
}

const onMouseDown = (e: MouseEvent) => {
  const target = e.target as HTMLElement
  if (target.closest('[data-node]')) return
  dragState.value = {
    x: e.clientX,
    y: e.clientY,
    ox: offset.value.x,
    oy: offset.value.y,
  }
}

const onMouseMove = (e: MouseEvent) => {
  if (!dragState.value) return
  offset.value = {
    x: dragState.value.ox + (e.clientX - dragState.value.x),
    y: dragState.value.oy + (e.clientY - dragState.value.y),
  }
}

const endDrag = () => {
  dragState.value = null
}

const zoomIn = () => {
  scale.value = Math.min(1.6, scale.value + 0.1)
}
const zoomOut = () => {
  scale.value = Math.max(0.5, scale.value - 0.1)
}
const reset = () => {
  scale.value = 1
  offset.value = { x: 24, y: 24 }
}

const path = (from: LaidOutNode, to: LaidOutNode) => {
  const sx = from.x + from.width
  const sy = from.y + from.height / 2
  const tx = to.x
  const ty = to.y + to.height / 2
  const cx = (sx + tx) / 2
  return `M ${sx} ${sy} C ${cx} ${sy}, ${cx} ${ty}, ${tx} ${ty}`
}

const nodeClass = (node: LaidOutNode) =>
  cn(
    'absolute rounded-xl border px-3 text-left transition-all duration-200',
    'flex items-center justify-center text-center text-xs font-medium leading-tight',
    'animate-node-pop hover:-translate-y-0.5 cursor-pointer',
    node.depth === 0
      ? 'bg-electric-400 text-white border-electric-400 shadow-glow font-display text-sm'
      : node.depth === 1
        ? 'bg-indigo-50 text-moon-50 border-electric-400/30 shadow-glow-sm'
        : 'bg-white text-moon-50 border-zinc-200 shadow-soft',
    props.selectedId === node.id && 'ring-2 ring-electric-400 ring-offset-2 ring-offset-white',
  )

const onSelect = (id: string) => {
  emit('select', id)
}

const onAdd = (id: string) => {
  if (props.readonly) return
  emit('addChild', id)
}

const onEdit = (id: string) => {
  if (props.readonly) return
  emit('edit', id)
}

watch(
  () => props.root?.id,
  () => {
    scale.value = 1
    offset.value = { x: 24, y: 24 }
  },
)
</script>

<template>
  <div
    class="relative h-full w-full overflow-hidden rounded-2xl border border-zinc-200 bg-zinc-50"
    @wheel.passive="onWheel"
    @mousedown="onMouseDown"
    @mousemove="onMouseMove"
    @mouseup="endDrag"
    @mouseleave="endDrag"
  >
    <div class="absolute inset-0 grid-bg opacity-30 pointer-events-none" />

    <div
      v-if="layout.nodes.length"
      class="absolute origin-top-left"
      :style="{
        transform: `translate(${offset.x}px, ${offset.y}px) scale(${scale})`,
        width: layout.width + 'px',
        height: layout.height + 'px',
      }"
    >
      <svg
        class="absolute left-0 top-0 pointer-events-none"
        :width="layout.width"
        :height="layout.height"
      >
        <defs>
          <linearGradient id="edge-grad" x1="0" x2="1">
            <stop offset="0%" stop-color="#4F46E5" stop-opacity="0.5" />
            <stop offset="100%" stop-color="#4F46E5" stop-opacity="0.15" />
          </linearGradient>
        </defs>
        <template v-for="edge in layout.edges" :key="edge.from + edge.to">
          <path
            :d="
              path(
                layout.nodes.find((n) => n.id === edge.from)!,
                layout.nodes.find((n) => n.id === edge.to)!,
              )
            "
            stroke="url(#edge-grad)"
            stroke-width="1.5"
            fill="none"
          />
        </template>
      </svg>

      <div
        v-for="node in layout.nodes"
        :key="node.id"
        data-node
        :style="{
          left: node.x + 'px',
          top: node.y + 'px',
          width: node.width + 'px',
          height: node.height + 'px',
        }"
        :class="nodeClass(node)"
        @click.stop="onSelect(node.id)"
        @dblclick.stop="onEdit(node.id)"
      >
        <span class="line-clamp-2">{{ node.title }}</span>
        <button
          v-if="!readonly && selectedId === node.id"
          class="absolute -right-3 top-1/2 grid h-6 w-6 -translate-y-1/2 place-items-center rounded-full border border-electric-400/60 bg-white text-electric-400 shadow-glow-sm transition-transform hover:scale-110"
          aria-label="添加子节点"
          @click.stop="onAdd(node.id)"
        >
          +
        </button>
      </div>
    </div>

    <div
      v-else
      class="flex h-full items-center justify-center text-sm text-mist-500"
    >
      <span>等待生成大纲…</span>
    </div>

    <!-- TOOLBAR -->
    <div
      class="absolute bottom-4 right-4 flex items-center gap-1 rounded-full border border-zinc-200 bg-white px-1.5 py-1 shadow-soft"
    >
      <button
        class="grid h-7 w-7 place-items-center rounded-full text-mist-400 hover:bg-zinc-100 hover:text-moon-50"
        aria-label="缩小"
        @click="zoomOut"
      >
        −
      </button>
      <span class="px-1 text-xs tabular-nums text-mist-400"
        >{{ Math.round(scale * 100) }}%</span
      >
      <button
        class="grid h-7 w-7 place-items-center rounded-full text-mist-400 hover:bg-zinc-100 hover:text-moon-50"
        aria-label="放大"
        @click="zoomIn"
      >
        +
      </button>
      <span class="mx-1 h-4 w-px bg-zinc-200" />
      <button
        class="rounded-full px-2 text-[11px] text-mist-400 hover:text-moon-50"
        @click="reset"
      >
        重置视图
      </button>
    </div>

    <div
      v-if="streaming"
      class="absolute left-4 top-4 inline-flex items-center gap-2 rounded-full border border-electric-400/30 bg-electric-400/10 px-3 py-1 text-xs text-electric-400"
    >
      <span class="inline-block h-1.5 w-1.5 animate-pulse rounded-full bg-electric-400" />
      AI 正在思考…
    </div>
  </div>
</template>
