/**
 * 用户与通知接口。
 */

import { http } from './client'
import type { AdminUser, AppNotification } from '@/types'

export interface UpdateUserPayload {
  nickname?: string
  avatarUrl?: string
  bio?: string
}

export interface CreateNotificationPayload {
  title: string
  body: string
  level?: 'info' | 'success' | 'warning'
  link?: string
}

export const userApi = {
  me: () => http.get<AdminUser>('/users/me'),

  update: (payload: UpdateUserPayload) => http.patch<AdminUser>('/users/me', payload),

  listNotifications: () => http.get<AppNotification[]>('/users/me/notifications'),

  pushNotification: (payload: CreateNotificationPayload) =>
    http.post<AppNotification>('/users/me/notifications', payload),

  markRead: (id: string) =>
    http.post<AppNotification>(`/users/me/notifications/${id}/read`, {}),

  markAllRead: () =>
    http.post<{ updated: number }>('/users/me/notifications/read-all', {}),
}
