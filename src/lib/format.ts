import { format, formatDistanceToNow } from 'date-fns'
import { zhCN } from 'date-fns/locale'

export function formatDate(value: string | number | Date): string {
  const d = typeof value === 'string' || typeof value === 'number' ? new Date(value) : value
  return format(d, 'yyyy-MM-dd HH:mm', { locale: zhCN })
}

export function formatRelative(value: string | number | Date): string {
  const d = typeof value === 'string' || typeof value === 'number' ? new Date(value) : value
  return formatDistanceToNow(d, { addSuffix: true, locale: zhCN })
}

export function formatFileSize(bytes: number): string {
  if (!Number.isFinite(bytes) || bytes <= 0) return '—'
  const units = ['B', 'KB', 'MB', 'GB']
  let i = 0
  let v = bytes
  while (v >= 1024 && i < units.length - 1) {
    v /= 1024
    i += 1
  }
  return `${v.toFixed(v >= 100 || i === 0 ? 0 : 1)} ${units[i]}`
}

export function formatDuration(seconds: number): string {
  if (!Number.isFinite(seconds) || seconds < 0) return '00:00'
  const m = Math.floor(seconds / 60)
  const s = Math.floor(seconds % 60)
  return `${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}`
}
