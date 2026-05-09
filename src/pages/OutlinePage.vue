<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { nanoid } from 'nanoid'
import {
  ArrowLeft,
  ArrowRight,
  RefreshCw,
  Plus,
  Trash2,
  Wand2,
  Save,
} from 'lucide-vue-next'
import PageShell from '@/components/layout/PageShell.vue'
import AppButton from '@/components/ui/AppButton.vue'
import AppCard from '@/components/ui/AppCard.vue'
import AppInput from '@/components/ui/AppInput.vue'
import AppStepper from '@/components/ui/AppStepper.vue'
import MindMapCanvas from '@/components/mindmap/MindMapCanvas.vue'
import { useProjectStore } from '@/stores/projects'
import { streamOutline, type StreamHandle } from '@/services/outlineMock'
import {
  cloneOutline,
  countNodes,
  findNode,
  findParent,
  maxDepth,
  recomputeDepth,
  removeNode,
} from '@/lib/outline'
import type { OutlineNode } from '@/types'

const route = useRoute()
const router = useRouter()
const projects = useProjectStore()

const projectId = computed(() => route.params.projectId as string)
const project = computed(() => projects.byId(projectId.value))

const root = ref<OutlineNode | null>(null)
const streaming = ref(false)
const selectedId = ref<string | null>(null)
const stream = ref<StreamHandle | null>(null)

const STEPS = [
  { key: 'outline', label: '大纲生成' },
  { key: 'config', label: '视频配置' },
  { key: 'progress', label: '生成视频' },
  { key: 'preview', label: '预览导出' },
]

const stats = computed(() => ({
  nodes: countNodes(root.value),
  depth: root.value ? maxDepth(root.value) + 1 : 0,
}))

const selectedNode = computed(() =>
  selectedId.value ? findNode(root.value, selectedId.value) : null,
)

const startStream = () => {
  if (!project.value) return
  root.value = null
  streaming.value = true
  selectedId.value = null
  stream.value?.cancel()
  const buffer = new Map<string, OutlineNode>()
  stream.value = streamOutline(project.value.topic, (chunk) => {
    if (chunk.type === 'node' && chunk.node) {
      const node: OutlineNode = { ...chunk.node, children: [] }
      buffer.set(node.id, node)
      if (node.parentId === null) {
        root.value = node
      } else {
        const parent = buffer.get(node.parentId)
        if (parent) {
          parent.children.push(node)
          root.value = root.value ? { ...root.value } : root.value
        }
      }
    }
    if (chunk.type === 'done') {
      streaming.value = false
      if (root.value) {
        recomputeDepth(root.value)
        projects.setOutline(projectId.value, cloneOutline(root.value)!)
        selectedId.value = root.value.id
      }
    }
  })
}

const regenerate = () => {
  if (streaming.value) return
  startStream()
}

const onSelect = (id: string) => {
  selectedId.value = id
}

const onAddChild = (id: string) => {
  const target = findNode(root.value, id)
  if (!target) return
  const child: OutlineNode = {
    id: `n-${nanoid(6)}`,
    parentId: target.id,
    title: '新节点',
    depth: target.depth + 1,
    children: [],
  }
  target.children.push(child)
  root.value = { ...root.value! }
  selectedId.value = child.id
}

const onEditNode = (id: string) => {
  selectedId.value = id
  setTimeout(() => {
    const input = document.getElementById('node-title-input') as HTMLInputElement | null
    input?.focus()
    input?.select()
  }, 50)
}

const updateTitle = (val: string) => {
  if (!selectedNode.value) return
  selectedNode.value.title = val
  root.value = { ...root.value! }
}

const updateNote = (val: string) => {
  if (!selectedNode.value) return
  selectedNode.value.note = val
  root.value = { ...root.value! }
}

const deleteSelected = () => {
  if (!selectedNode.value || !root.value) return
  if (selectedNode.value.id === root.value.id) {
    alert('根节点不能删除')
    return
  }
  const parent = findParent(root.value, selectedNode.value.id)
  removeNode(root.value, selectedNode.value.id)
  root.value = { ...root.value! }
  selectedId.value = parent?.id ?? root.value.id
}

const addSibling = () => {
  if (!selectedNode.value || !root.value) return
  if (selectedNode.value.id === root.value.id) {
    onAddChild(root.value.id)
    return
  }
  const parent = findParent(root.value, selectedNode.value.id)
  if (!parent) return
  const sib: OutlineNode = {
    id: `n-${nanoid(6)}`,
    parentId: parent.id,
    title: '新节点',
    depth: parent.depth + 1,
    children: [],
  }
  parent.children.push(sib)
  root.value = { ...root.value! }
  selectedId.value = sib.id
}

const save = () => {
  if (!root.value || !project.value) return
  recomputeDepth(root.value)
  projects.setOutline(projectId.value, cloneOutline(root.value)!)
}

const goNext = () => {
  if (!root.value) return
  save()
  router.push({ name: 'config', params: { projectId: projectId.value } })
}

onMounted(() => {
  if (!project.value) {
    router.replace({ name: 'dashboard' })
    return
  }
  if (project.value.outline) {
    root.value = cloneOutline(project.value.outline)
    selectedId.value = root.value!.id
  } else {
    startStream()
  }
})

onUnmounted(() => {
  stream.value?.cancel()
})
</script>

<template>
  <PageShell hide-footer full-height>
    <div class="container-page flex h-full flex-col gap-6 py-8">
      <!-- HEADER -->
      <div class="flex flex-col gap-4">
        <div class="flex items-center justify-between gap-3">
          <button
            class="inline-flex items-center gap-1.5 text-sm text-mist-400 hover:text-electric-400"
            @click="router.push('/dashboard')"
          >
            <ArrowLeft class="h-4 w-4" /> 返回工作台
          </button>
          <div class="flex items-center gap-2">
            <AppButton
              variant="secondary"
              size="sm"
              :disabled="streaming"
              @click="regenerate"
            >
              <RefreshCw class="h-4 w-4" :class="streaming && 'animate-spin'" />
              重新生成
            </AppButton>
            <AppButton variant="ghost" size="sm" @click="save">
              <Save class="h-4 w-4" /> 保存
            </AppButton>
            <AppButton
              variant="primary"
              size="sm"
              :disabled="streaming || !root"
              @click="goNext"
            >
              下一步 · 视频配置 <ArrowRight class="h-4 w-4" />
            </AppButton>
          </div>
        </div>
        <AppStepper :steps="STEPS" :current="0" />
      </div>

      <!-- TOPIC -->
      <AppCard class="!p-5">
        <div class="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
          <div class="flex items-center gap-3">
            <span
              class="grid h-9 w-9 place-items-center rounded-md border border-electric-400/30 bg-electric-400/10"
            >
              <Wand2 class="h-4 w-4 text-electric-400" />
            </span>
            <div>
              <p class="text-xs uppercase tracking-wider text-mist-500">
                当前主题
              </p>
              <h2 class="font-display text-lg font-semibold text-moon-50">
                {{ project?.topic ?? '—' }}
              </h2>
            </div>
          </div>
          <div class="flex items-center gap-6 text-xs text-mist-400">
            <div>
              <span class="text-mist-500">节点</span>
              <span class="ml-2 font-display text-base text-moon-50">{{
                stats.nodes
              }}</span>
            </div>
            <div>
              <span class="text-mist-500">层级</span>
              <span class="ml-2 font-display text-base text-moon-50">{{
                stats.depth
              }}</span>
            </div>
          </div>
        </div>
      </AppCard>

      <!-- WORKSPACE -->
      <div class="grid flex-1 grid-cols-1 gap-6 lg:grid-cols-[1fr_320px]">
        <div class="min-h-[520px]">
          <MindMapCanvas
            :root="root"
            :selected-id="selectedId"
            :streaming="streaming"
            @select="onSelect"
            @add-child="onAddChild"
            @edit="onEditNode"
          />
        </div>

        <!-- INSPECTOR -->
        <AppCard class="!p-5 h-fit">
          <div class="mb-4 flex items-center justify-between">
            <h3 class="font-display text-base font-semibold">节点编辑</h3>
            <span class="text-xs text-mist-500">双击节点可编辑</span>
          </div>

          <template v-if="selectedNode">
            <div class="space-y-4">
              <div>
                <label
                  class="mb-1.5 block text-xs uppercase tracking-wider text-mist-500"
                  >标题</label
                >
                <AppInput
                  id="node-title-input"
                  size="sm"
                  :model-value="selectedNode.title"
                  @update:model-value="updateTitle"
                />
              </div>
              <div>
                <label
                  class="mb-1.5 block text-xs uppercase tracking-wider text-mist-500"
                  >备注（可选）</label
                >
                <textarea
                  class="block min-h-[88px] w-full rounded-md border border-zinc-200 bg-white px-3 py-2 text-sm text-moon-50 placeholder:text-mist-500 outline-none transition-colors focus:border-electric-400/60"
                  placeholder="为该节点补充更多解释，将被纳入配音脚本…"
                  :value="selectedNode.note ?? ''"
                  @input="(e) => updateNote((e.target as HTMLTextAreaElement).value)"
                />
              </div>

              <div class="grid grid-cols-2 gap-2">
                <AppButton variant="secondary" size="sm" @click="onAddChild(selectedNode.id)">
                  <Plus class="h-4 w-4" /> 子节点
                </AppButton>
                <AppButton variant="secondary" size="sm" @click="addSibling">
                  <Plus class="h-4 w-4" /> 同级
                </AppButton>
                <AppButton
                  variant="danger"
                  size="sm"
                  class="col-span-2"
                  :disabled="root && selectedNode.id === root.id"
                  @click="deleteSelected"
                >
                  <Trash2 class="h-4 w-4" /> 删除节点
                </AppButton>
              </div>

              <div
                class="rounded-lg border border-zinc-200 bg-zinc-50 p-3 text-[11px] leading-relaxed text-mist-500"
              >
                <p>📌 操作提示</p>
                <ul class="mt-1 space-y-1">
                  <li>· 单击节点选中并查看详情</li>
                  <li>· 选中后右侧 <kbd>+</kbd> 按钮添加子节点</li>
                  <li>· 拖拽空白处可平移画布，<kbd>Ctrl/Cmd</kbd> + 滚轮缩放</li>
                </ul>
              </div>
            </div>
          </template>

          <template v-else>
            <div class="py-12 text-center text-sm text-mist-500">
              <p>选择一个节点开始编辑</p>
            </div>
          </template>
        </AppCard>
      </div>
    </div>
  </PageShell>
</template>
