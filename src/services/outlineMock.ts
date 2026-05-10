import { nanoid } from 'nanoid'
import type { OutlineNode, Scene } from '@/types'

interface RawOutline {
  title: string
  children?: RawOutline[]
}

interface RawScene {
  title: string
  content: string
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

const SCENE_TEMPLATES: Record<string, RawScene[]> = {
  人工智能发展史: [
    { title: '开篇：什么是人工智能', content: '从图灵的"机器能思考吗"出发，介绍 AI 的定义、目标，以及它在今天为什么如此重要。' },
    { title: '萌芽期（1950 之前）', content: '图灵测试与神经元数学模型的诞生，奠定了"用机器模拟思维"的早期思想基础。' },
    { title: '黄金年代（1956-1974）', content: '达特茅斯会议正式确立 AI 学科，感知机、专家系统初现，乐观情绪空前高涨。' },
    { title: '第一次寒冬（1974-1980）', content: '算力瓶颈与研究经费收紧，AI 跌入低谷，但理论积累仍在悄然推进。' },
    { title: '复兴与第二次寒冬（1980-2010）', content: '专家系统商业化短暂繁荣，统计机器学习兴起，GPU 与大数据为下一波浪潮埋下伏笔。' },
    { title: '深度学习革命（2010-至今）', content: 'ImageNet、AlphaGo、Transformer 与大模型时代，AI 进入指数级爆发期。' },
    { title: '展望：通向通用智能', content: '多模态、具身智能、AGI 的路径与挑战，AI 与人类社会如何共同进化。' },
  ],
}

const GENERIC_SCENES: RawScene[] = [
  { title: '开篇引入', content: '用一个生活化的场景或反常识的事实切入主题，迅速抓住观众注意力。' },
  { title: '背景与意义', content: '介绍这个主题的产生背景、为什么值得了解，以及最常见的误解。' },
  { title: '核心概念', content: '给出简洁的定义和关键术语，并用一个比喻帮助理解。' },
  { title: '关键原理', content: '拆解核心机制：它是如何运作的，背后的逻辑或公式是什么。' },
  { title: '典型案例', content: '通过 1-2 个真实案例，展示该原理在现实世界中的应用形态。' },
  { title: '常见误区', content: '列举初学者容易踩的坑，帮助观众建立正确的认知模型。' },
  { title: '未来趋势', content: '展望前沿方向、潜在挑战，以及给观众的进一步学习建议。' },
  { title: '结尾收束', content: '用一句话总结全篇，并抛出一个引人思考的问题或行动号召。' },
]

function pickScenes(topic: string): RawScene[] {
  const trimmed = topic.trim()
  if (SCENE_TEMPLATES[trimmed]) return SCENE_TEMPLATES[trimmed]
  return GENERIC_SCENES.map((s) => ({ ...s }))
}

export interface SceneStreamChunk {
  type: 'scene' | 'done'
  scene?: Scene
  total?: number
}

export function streamScenes(
  topic: string,
  onChunk: (chunk: SceneStreamChunk) => void,
): StreamHandle {
  const raw = pickScenes(topic)
  const scenes: Scene[] = raw.map((r, i) => ({
    id: `s-${nanoid(6)}`,
    index: i,
    title: r.title,
    content: r.content,
  }))

  let cancelled = false
  let i = 0

  const tick = () => {
    if (cancelled) return
    if (i >= scenes.length) {
      onChunk({ type: 'done', total: scenes.length })
      return
    }
    onChunk({ type: 'scene', scene: scenes[i] })
    i += 1
    const delay = i === 1 ? 320 : 180 + Math.random() * 200
    setTimeout(tick, delay)
  }

  setTimeout(tick, 220)

  return {
    cancel() {
      cancelled = true
    },
  }
}

export function generateScenesSync(topic: string): Scene[] {
  return pickScenes(topic).map((r, i) => ({
    id: `s-${nanoid(6)}`,
    index: i,
    title: r.title,
    content: r.content,
  }))
}
