import type { OutlineNode } from '@/types'

export function countNodes(node: OutlineNode | null): number {
  if (!node) return 0
  let count = 1
  for (const child of node.children) count += countNodes(child)
  return count
}

export function flattenNodes(node: OutlineNode | null): OutlineNode[] {
  if (!node) return []
  const list: OutlineNode[] = [node]
  for (const child of node.children) list.push(...flattenNodes(child))
  return list
}

export function findNode(
  root: OutlineNode | null,
  id: string,
): OutlineNode | null {
  if (!root) return null
  if (root.id === id) return root
  for (const child of root.children) {
    const found = findNode(child, id)
    if (found) return found
  }
  return null
}

export function findParent(
  root: OutlineNode | null,
  id: string,
): OutlineNode | null {
  if (!root) return null
  for (const child of root.children) {
    if (child.id === id) return root
    const inner = findParent(child, id)
    if (inner) return inner
  }
  return null
}

export function removeNode(root: OutlineNode | null, id: string): boolean {
  if (!root) return false
  const idx = root.children.findIndex((c) => c.id === id)
  if (idx >= 0) {
    root.children.splice(idx, 1)
    return true
  }
  for (const child of root.children) {
    if (removeNode(child, id)) return true
  }
  return false
}

export function cloneOutline(node: OutlineNode | null): OutlineNode | null {
  if (!node) return null
  return JSON.parse(JSON.stringify(node)) as OutlineNode
}

export function recomputeDepth(node: OutlineNode, depth = 0): void {
  node.depth = depth
  for (const child of node.children) recomputeDepth(child, depth + 1)
}

export function maxDepth(node: OutlineNode | null): number {
  if (!node) return 0
  if (!node.children.length) return node.depth
  return Math.max(...node.children.map((c) => maxDepth(c)))
}
