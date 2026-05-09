import type { OutlineNode } from '@/types'

export interface LaidOutNode {
  id: string
  parentId: string | null
  title: string
  depth: number
  x: number
  y: number
  width: number
  height: number
}

export interface MindmapLayout {
  nodes: LaidOutNode[]
  edges: Array<{ from: string; to: string }>
  width: number
  height: number
}

const LEVEL_GAP = 220
const NODE_GAP_Y = 18
const NODE_PADDING_X = 18
const ROOT_WIDTH = 200
const NODE_WIDTH_BY_DEPTH: Record<number, number> = {
  0: 200,
  1: 184,
  2: 168,
  3: 156,
  4: 148,
}
const NODE_HEIGHT = 56

function widthOf(depth: number): number {
  return NODE_WIDTH_BY_DEPTH[depth] ?? 140
}

function heightOf(): number {
  return NODE_HEIGHT
}

interface SubtreeMetric {
  height: number
}

function measure(node: OutlineNode, cache: Map<string, SubtreeMetric>): SubtreeMetric {
  if (!node.children.length) {
    const m = { height: heightOf() }
    cache.set(node.id, m)
    return m
  }
  let total = 0
  for (let i = 0; i < node.children.length; i += 1) {
    const child = node.children[i]
    total += measure(child, cache).height
    if (i < node.children.length - 1) total += NODE_GAP_Y
  }
  total = Math.max(total, heightOf())
  const m = { height: total }
  cache.set(node.id, m)
  return m
}

function place(
  node: OutlineNode,
  depth: number,
  startY: number,
  metrics: Map<string, SubtreeMetric>,
  out: LaidOutNode[],
  edges: Array<{ from: string; to: string }>,
  parentId: string | null,
): void {
  const m = metrics.get(node.id)!
  const x = depth * LEVEL_GAP + NODE_PADDING_X
  const w = widthOf(depth)
  const h = heightOf()
  const y = startY + m.height / 2 - h / 2
  out.push({
    id: node.id,
    parentId,
    title: node.title,
    depth,
    x,
    y,
    width: w,
    height: h,
  })
  if (parentId) edges.push({ from: parentId, to: node.id })
  let cursor = startY
  for (const child of node.children) {
    const cm = metrics.get(child.id)!
    place(child, depth + 1, cursor, metrics, out, edges, node.id)
    cursor += cm.height + NODE_GAP_Y
  }
}

export function layoutMindmap(root: OutlineNode | null): MindmapLayout {
  if (!root) {
    return { nodes: [], edges: [], width: 0, height: 0 }
  }
  const metrics = new Map<string, SubtreeMetric>()
  measure(root, metrics)
  const nodes: LaidOutNode[] = []
  const edges: Array<{ from: string; to: string }> = []
  place(root, 0, 0, metrics, nodes, edges, null)

  let maxX = 0
  let maxY = 0
  for (const n of nodes) {
    maxX = Math.max(maxX, n.x + n.width)
    maxY = Math.max(maxY, n.y + n.height)
  }
  return {
    nodes,
    edges,
    width: maxX + NODE_PADDING_X,
    height: maxY + NODE_PADDING_X,
  }
}

export const MINDMAP_CONSTANTS = {
  LEVEL_GAP,
  NODE_GAP_Y,
  ROOT_WIDTH,
  NODE_HEIGHT,
}
