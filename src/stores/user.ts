import { defineStore } from 'pinia'
import type { AdminUser, AppNotification } from '@/types'
import { userApi, type CreateNotificationPayload, type UpdateUserPayload } from '@/lib/api'

const FALLBACK_USER: AdminUser = {
  id: 'admin',
  nickname: 'Admin',
  avatarUrl:
    'https://trae-api-cn.mchost.guru/api/ide/v1/text_to_image?prompt=futuristic%20minimalist%20abstract%20avatar%20portrait%2C%20cyan%20glow%20highlights%2C%20deep%20navy%20background%2C%20geometric%20shapes&image_size=square',
  bio: '默认内置管理员，掌管全部本地项目空间。',
  role: 'admin',
}

interface State {
  user: AdminUser
  notifications: AppNotification[]
  loaded: boolean
  loading: boolean
  error: string | null
}

export const useUserStore = defineStore('user', {
  state: (): State => ({
    user: FALLBACK_USER,
    notifications: [],
    loaded: false,
    loading: false,
    error: null,
  }),
  getters: {
    unreadCount: (s) => s.notifications.filter((n) => !n.read).length,
  },
  actions: {
    async fetchMe(force = false): Promise<AdminUser> {
      if (this.loaded && !force) return this.user
      this.loading = true
      this.error = null
      try {
        const [me, notifications] = await Promise.all([
          userApi.me(),
          userApi.listNotifications(),
        ])
        this.user = me
        this.notifications = notifications
        this.loaded = true
        return me
      } catch (err) {
        this.error = err instanceof Error ? err.message : '加载用户信息失败'
        throw err
      } finally {
        this.loading = false
      }
    },
    async updateMe(payload: UpdateUserPayload): Promise<AdminUser> {
      this.error = null
      const next = await userApi.update(payload)
      this.user = next
      return next
    },
    async pushNotification(payload: CreateNotificationPayload): Promise<AppNotification> {
      const created = await userApi.pushNotification(payload)
      this.notifications.unshift(created)
      return created
    },
    async markRead(id: string): Promise<void> {
      const updated = await userApi.markRead(id)
      const idx = this.notifications.findIndex((n) => n.id === id)
      if (idx >= 0) this.notifications[idx] = updated
    },
    async markAllRead(): Promise<void> {
      await userApi.markAllRead()
      this.notifications = this.notifications.map((n) => ({ ...n, read: true }))
    },
  },
})
