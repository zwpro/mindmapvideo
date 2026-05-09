import { defineStore } from 'pinia'
import type { AdminUser, AppNotification } from '@/types'

const ADMIN: AdminUser = {
  id: 'admin',
  nickname: 'Admin',
  avatarUrl:
    'https://trae-api-cn.mchost.guru/api/ide/v1/text_to_image?prompt=futuristic%20minimalist%20abstract%20avatar%20portrait%2C%20cyan%20glow%20highlights%2C%20deep%20navy%20background%2C%20geometric%20shapes&image_size=square',
  bio: '默认内置管理员，掌管全部本地项目空间。',
  role: 'admin',
}

export const useUserStore = defineStore('user', {
  state: () => ({
    user: ADMIN as AdminUser,
    notifications: [] as AppNotification[],
  }),
  getters: {
    unreadCount: (s) => s.notifications.filter((n) => !n.read).length,
  },
  actions: {
    pushNotification(payload: Omit<AppNotification, 'id' | 'read' | 'createdAt'>) {
      const id = `n-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`
      this.notifications.unshift({
        id,
        read: false,
        createdAt: new Date().toISOString(),
        ...payload,
      })
    },
    markRead(id: string) {
      const item = this.notifications.find((n) => n.id === id)
      if (item) item.read = true
    },
    markAllRead() {
      this.notifications.forEach((n) => (n.read = true))
    },
  },
  persist: {
    key: 'mindmap.user',
  },
})
