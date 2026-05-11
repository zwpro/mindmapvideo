/**
 * 基于 fetch 的轻量 HTTP 客户端。
 *
 * 特性：
 * - 自动拼接 API_BASE + API_PREFIX
 * - 自动带 JSON header、序列化 body
 * - 统一错误对象 ApiError,组件层可用 instanceof 判断
 * - 支持 AbortSignal 取消（用于切页/组件卸载时中断请求）
 * - 预留 token 注入位（从 localStorage 读；后续可换成 pinia store）
 */

import { buildUrl } from './config'

export interface ApiErrorPayload {
  detail?: string | Array<{ msg: string; loc?: unknown[] }>
  [key: string]: unknown
}

/** 统一的业务错误，组件层可 catch 后判断 status 决定如何提示 */
export class ApiError extends Error {
  status: number
  payload?: ApiErrorPayload

  constructor(status: number, message: string, payload?: ApiErrorPayload) {
    super(message)
    this.name = 'ApiError'
    this.status = status
    this.payload = payload
  }
}

export interface RequestOptions extends Omit<RequestInit, 'body' | 'headers'> {
  /** JSON body，会自动 stringify */
  json?: unknown
  /** 原始 body（与 json 互斥），用于上传等场景 */
  body?: BodyInit
  /** 额外 header */
  headers?: Record<string, string>
  /** URL query，自动 encode */
  query?: Record<string, string | number | boolean | undefined | null>
  /** 超时毫秒数，默认 10 分钟 */
  timeoutMs?: number
}

const DEFAULT_TIMEOUT = 10 * 60 * 1000 // 10 分钟

function getAuthToken(): string | null {
  try {
    return localStorage.getItem('mindmap.auth.token')
  } catch {
    return null
  }
}

function buildQuery(query?: RequestOptions['query']): string {
  if (!query) return ''
  const usp = new URLSearchParams()
  for (const [k, v] of Object.entries(query)) {
    if (v === undefined || v === null) continue
    usp.append(k, String(v))
  }
  const s = usp.toString()
  return s ? `?${s}` : ''
}

async function parseBody(res: Response): Promise<unknown> {
  const ct = res.headers.get('content-type') ?? ''
  if (ct.includes('application/json')) {
    try {
      return await res.json()
    } catch {
      return null
    }
  }
  const text = await res.text()
  return text || null
}

function extractErrorMessage(payload: unknown, fallback: string): string {
  if (payload && typeof payload === 'object') {
    const detail = (payload as ApiErrorPayload).detail
    if (typeof detail === 'string') return detail
    if (Array.isArray(detail) && detail.length > 0) {
      return detail.map((d) => d.msg).filter(Boolean).join('; ') || fallback
    }
  }
  if (typeof payload === 'string' && payload.trim()) return payload
  return fallback
}

export async function request<T = unknown>(
  path: string,
  options: RequestOptions = {},
): Promise<T> {
  const { json, body, headers, query, timeoutMs = DEFAULT_TIMEOUT, signal, ...rest } = options

  const url = buildUrl(path) + buildQuery(query)

  const finalHeaders: Record<string, string> = {
    Accept: 'application/json',
    ...headers,
  }

  let finalBody: BodyInit | undefined
  if (json !== undefined) {
    finalHeaders['Content-Type'] = 'application/json'
    finalBody = JSON.stringify(json)
  } else if (body !== undefined) {
    finalBody = body
  }

  const token = getAuthToken()
  if (token && !finalHeaders.Authorization) {
    finalHeaders.Authorization = `Bearer ${token}`
  }

  // 组合外部 signal 与超时 signal
  const controller = new AbortController()
  const timeoutId = setTimeout(() => controller.abort(), timeoutMs)
  if (signal) {
    if (signal.aborted) controller.abort()
    else signal.addEventListener('abort', () => controller.abort(), { once: true })
  }

  let res: Response
  try {
    res = await fetch(url, {
      ...rest,
      headers: finalHeaders,
      body: finalBody,
      signal: controller.signal,
    })
  } catch (err) {
    clearTimeout(timeoutId)
    if ((err as Error).name === 'AbortError') {
      throw new ApiError(0, '请求已取消或超时')
    }
    throw new ApiError(0, `网络错误：${(err as Error).message}`)
  }
  clearTimeout(timeoutId)

  const payload = await parseBody(res)

  if (!res.ok) {
    const msg = extractErrorMessage(payload, `HTTP ${res.status}`)
    throw new ApiError(res.status, msg, payload as ApiErrorPayload)
  }

  return payload as T
}

/** 便捷方法 */
export const http = {
  get: <T = unknown>(path: string, options?: RequestOptions) =>
    request<T>(path, { ...options, method: 'GET' }),
  post: <T = unknown>(path: string, json?: unknown, options?: RequestOptions) =>
    request<T>(path, { ...options, method: 'POST', json }),
  put: <T = unknown>(path: string, json?: unknown, options?: RequestOptions) =>
    request<T>(path, { ...options, method: 'PUT', json }),
  patch: <T = unknown>(path: string, json?: unknown, options?: RequestOptions) =>
    request<T>(path, { ...options, method: 'PATCH', json }),
  delete: <T = unknown>(path: string, options?: RequestOptions) =>
    request<T>(path, { ...options, method: 'DELETE' }),
}
