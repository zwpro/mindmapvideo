import { nanoid } from 'nanoid'
import type { OutlineNode } from '@/types'

interface RawOutline {
  title: string
  children?: RawOutline[]
}

const TEMPLATES: Record<string, RawOutline> = {
  人工智能发展史: {
    title: '人工智能发展史',
    children: [
      {
        title: '萌芽期（1950 之前）',
        children: [
          { title: '图灵测试与思想实验' },
          { title: '神经元数学模型' },
        ],
      },
      {
        title: '黄金年代（1956-1974）',
        children: [
          { title: '达特茅斯会议奠定学科' },
          { title: '感知机与早期机器学习' },
          { title: '专家系统初现' },
        ],
      },
      {
        title: '第一次寒冬（1974-1980）',
        children: [
          { title: '算力瓶颈' },
          { title: '研究经费收紧' },
        ],
      },
      {
        title: '复兴与第二次寒冬（1980-2010）',
        children: [
          { title: '专家系统商业化' },
          { title: '统计机器学习兴起' },
          { title: 'GPU + 大数据萌芽' },
        ],
      },
      {
        title: '深度学习革命（2010-至今）',
        children: [
          { title: 'ImageNet 与 CNN 突破' },
          { title: 'AlphaGo 与强化学习' },
          { title: 'Transformer 与大模型时代' },
          { title: '多模态与具身智能' },
        ],
      },
    ],
  },
}

const GENERIC: RawOutline = {
  title: '主题概览',
  children: [
    {
      title: '背景与意义',
      children: [
        { title: '产生背景' },
        { title: '现实意义' },
        { title: '常见误解' },
      ],
    },
    {
      title: '核心概念',
      children: [
        { title: '基础定义' },
        { title: '关键术语' },
        { title: '与相邻概念的区别' },
      ],
    },
    {
      title: '关键原理',
      children: [
        { title: '运行机制' },
        { title: '典型流程' },
        { title: '数学/逻辑基础' },
      ],
    },
    {
      title: '实践应用',
      children: [
        { title: '行业落地案例' },
        { title: '工具与框架' },
        { title: '实操步骤' },
      ],
    },
    {
      title: '未来趋势',
      children: [
        { title: '前沿方向' },
        { title: '常见挑战' },
        { title: '学习路径建议' },
      ],
    },
  ],
}

function pickTemplate(topic: string): RawOutline {
  const trimmed = topic.trim()
  if (TEMPLATES[trimmed]) return TEMPLATES[trimmed]
  return { ...GENERIC, title: trimmed || GENERIC.title }
}

export interface OutlineStreamChunk {
  type: 'node' | 'done'
  node?: OutlineNode
  rootId?: string
}

function buildTree(raw: RawOutline, parentId: string | null, depth: number): OutlineNode {
  const node: OutlineNode = {
    id: `n-${nanoid(6)}`,
    parentId,
    title: raw.title,
    depth,
    children: [],
  }
  if (raw.children) {
    node.children = raw.children.map((c) => buildTree(c, node.id, depth + 1))
  }
  return node
}

function flatten(node: OutlineNode): OutlineNode[] {
  const list: OutlineNode[] = [node]
  for (const child of node.children) list.push(...flatten(child))
  return list
}

export interface StreamHandle {
  cancel(): void
}

export function streamOutline(
  topic: string,
  onChunk: (chunk: OutlineStreamChunk) => void,
): StreamHandle {
  const tree = buildTree(pickTemplate(topic), null, 0)
  const flat = flatten(tree)

  let cancelled = false
  let i = 0

  const tick = () => {
    if (cancelled) return
    if (i >= flat.length) {
      onChunk({ type: 'done', rootId: tree.id })
      return
    }
    const original = flat[i]
    const lite: OutlineNode = {
      id: original.id,
      parentId: original.parentId,
      title: original.title,
      depth: original.depth,
      children: [],
    }
    onChunk({ type: 'node', node: lite })
    i += 1
    const delay = i === 1 ? 320 : 140 + Math.random() * 200
    setTimeout(tick, delay)
  }

  setTimeout(tick, 220)

  return {
    cancel() {
      cancelled = true
    },
  }
}

export function generateOutlineSync(topic: string): OutlineNode {
  return buildTree(pickTemplate(topic), null, 0)
}
