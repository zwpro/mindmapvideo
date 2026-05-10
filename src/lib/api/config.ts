/**
 * 运行时 API 配置。
 *
 * 所有请求都要经过 buildUrl() 拼接 base + prefix + path,
 * 这样组件层只关心业务路径（/projects、/scenes 等）,不感知域名差异。
 */

const rawBase = (import.meta.env.VITE_API_BASE_URL ?? '').trim()
const rawPrefix = (import.meta.env.VITE_API_PREFIX ?? '/api/v1').trim()

/** 去掉尾斜杠，避免拼接出 //path */
function stripTrailingSlash(s: string): string {
  return s.endsWith('/') ? s.slice(0, -1) : s
}

/** 确保以 / 开头 */
function ensureLeadingSlash(s: string): string {
  return s.startsWith('/') ? s : `/${s}`
}

/**
 * 开发环境：VITE_API_BASE_URL 留空，走相对路径，由 Vite proxy 转发；
 * 生产环境：VITE_API_BASE_URL = https://api.xxx.com，浏览器直连后端。
 */
export const API_BASE = stripTrailingSlash(rawBase)
export const API_PREFIX = ensureLeadingSlash(stripTrailingSlash(rawPrefix))

/** 拼出最终 URL，path 以 / 开头，如 "/projects" */
export function buildUrl(path: string): string {
  const p = ensureLeadingSlash(path)
  return `${API_BASE}${API_PREFIX}${p}`
}

/** 用于非 v1 接口（如 /health） */
export function buildRawUrl(path: string): string {
  const p = ensureLeadingSlash(path)
  return `${API_BASE}${p}`
}

export const APP_ENV = import.meta.env.VITE_APP_ENV ?? 'development'
export const IS_DEV = APP_ENV === 'development'
