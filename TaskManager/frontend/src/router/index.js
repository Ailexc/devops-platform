import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  {
    path: '/',
    redirect: '/dashboard',
  },
  {
    path: '/dashboard',
    name: 'Dashboard',
    component: () => import('../views/MonitorDashboard.vue'),
  },
  {
    path: '/tasks',
    name: 'Tasks',
    component: () => import('../views/TaskManagement.vue'),
  },
  {
    path: '/history',
    name: 'History',
    component: () => import('../views/ExecutionHistory.vue'),
  },
  {
    path: '/history/:id',
    name: 'HistoryDetail',
    component: () => import('../views/HistoryDetail.vue'),
  },
  {
    path: '/docs',
    name: 'Docs',
    component: () => import('../views/SystemDocs.vue'),
  },
  {
    path: '/interview',
    name: 'Interview',
    component: () => import('../views/InterviewGuide.vue'),
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

export default router
