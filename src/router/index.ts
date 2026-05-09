import { createRouter, createWebHistory, type RouteRecordRaw } from 'vue-router'

const routes: RouteRecordRaw[] = [
  {
    path: '/',
    name: 'home',
    component: () => import('@/pages/HomePage.vue'),
  },
  {
    path: '/dashboard',
    name: 'dashboard',
    component: () => import('@/pages/DashboardPage.vue'),
  },
  {
    path: '/outline/:projectId',
    name: 'outline',
    component: () => import('@/pages/OutlinePage.vue'),
    props: true,
  },
  {
    path: '/config/:projectId',
    name: 'config',
    component: () => import('@/pages/ConfigPage.vue'),
    props: true,
  },
  {
    path: '/progress/:taskId',
    name: 'progress',
    component: () => import('@/pages/ProgressPage.vue'),
    props: true,
  },
  {
    path: '/preview/:videoId',
    name: 'preview',
    component: () => import('@/pages/PreviewPage.vue'),
    props: true,
  },
  {
    path: '/profile',
    name: 'profile',
    component: () => import('@/pages/ProfilePage.vue'),
  },
  {
    path: '/:pathMatch(.*)*',
    name: 'not-found',
    component: () => import('@/pages/NotFoundPage.vue'),
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
  scrollBehavior(_to, _from, savedPosition) {
    if (savedPosition) return savedPosition
    return { top: 0 }
  },
})

export default router
