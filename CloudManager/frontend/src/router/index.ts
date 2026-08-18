import { createRouter, createWebHistory } from 'vue-router'
import type { RouteRecordRaw } from 'vue-router'

const routes: RouteRecordRaw[] = [
  {
    path: '/login',
    name: 'Login',
    component: () => import('@/views/login/index.vue'),
    meta: { title: '登录', hidden: true },
  },
  {
    path: '/',
    component: () => import('@/layouts/ConsoleLayout.vue'),
    redirect: '/dashboard',
    children: [
      {
        path: 'dashboard',
        name: 'Dashboard',
        component: () => import('@/views/dashboard/index.vue'),
        meta: { title: '工作台', icon: 'DashboardOutlined' },
      },
      {
        path: 'compute/instances',
        name: 'Instances',
        component: () => import('@/views/compute/Instances.vue'),
        meta: { title: '云主机', icon: 'CloudServerOutlined' },
      },
      {
        path: 'compute/network',
        name: 'Network',
        component: () => import('@/views/compute/Network.vue'),
        meta: { title: '网络', icon: 'GlobalOutlined' },
      },
      {
        path: 'ticket/list',
        name: 'TicketList',
        component: () => import('@/views/ticket/TicketList.vue'),
        meta: { title: '工单中心', icon: 'FileTextOutlined' },
      },
      {
        path: 'ticket/detail/:id',
        name: 'TicketDetail',
        component: () => import('@/views/ticket/TicketDetail.vue'),
        meta: { title: '工单详情', hidden: true },
      },
      {
        path: 'audit/logs',
        name: 'AuditLogs',
        component: () => import('@/views/audit/Logs.vue'),
        meta: { title: '操作记录', icon: 'AuditOutlined' },
      },
      {
        path: 'catalog',
        name: 'Catalog',
        component: () => import('@/views/catalog/index.vue'),
        meta: { title: '服务目录', icon: 'AppstoreOutlined' },
      },
      {
        path: 'cost/trends',
        name: 'CostTrends',
        component: () => import('@/views/cost/Trends.vue'),
        meta: { title: '成本趋势', icon: 'MoneyCollectOutlined' },
      },
      {
        path: 'cost/overview',
        name: 'CostOverview',
        component: () => import('@/views/cost/Overview.vue'),
        meta: { title: '成本优化总览', icon: 'DashboardOutlined' },
      },
      {
        path: 'cost/rules',
        name: 'CostRules',
        component: () => import('@/views/cost/RuleConfig.vue'),
        meta: { title: '规则配置', icon: 'SettingOutlined' },
      },
      {
        path: 'cost/reports',
        name: 'CostReports',
        component: () => import('@/views/cost/ReportCenter.vue'),
        meta: { title: '分析报告', icon: 'FileTextOutlined' },
      },
      {
        path: 'cost/share',
        name: 'CostShare',
        component: () => import('@/views/cost/ShareDetail.vue'),
        meta: { title: '成本分摊明细', icon: 'PieChartOutlined', hidden: true },
      },
      {
        path: 'cost/suggestions',
        redirect: '/cost/overview',
        meta: { hidden: true },
      },
      {
        path: 'compute/topology',
        name: 'Topology',
        component: () => import('@/views/compute/Topology.vue'),
        meta: { title: '资源拓扑', hidden: true },
      },
      {
        path: 'applications',
        name: 'Applications',
        component: () => import('@/views/applications/List.vue'),
        meta: { title: '应用中心', icon: 'AppstoreOutlined' },
      },
      {
        path: 'applications/:id',
        name: 'ApplicationDetail',
        redirect: (to) => ({ path: '/applications', query: { app: to.params.id } }),
        meta: { title: '应用中心', hidden: true },
      },
      {
        path: 'environments/:id',
        name: 'EnvironmentDetail',
        component: () => import('@/views/environments/Detail.vue'),
        meta: { title: '环境详情', hidden: true },
      },
      {
        path: 'scenarios',
        name: 'Scenarios',
        component: () => import('@/views/scenario/List.vue'),
        meta: { title: '场景中心', icon: 'ThunderboltOutlined' },
      },
      {
        path: 'scenarios/:id',
        name: 'ScenarioDetail',
        component: () => import('@/views/scenario/Detail.vue'),
        meta: { title: '场景详情', hidden: true },
      },
      {
        path: 'knowledge/docs',
        name: 'KnowledgeDocs',
        component: () => import('@/views/knowledge/Docs.vue'),
        meta: { title: '系统文档', icon: 'BookOutlined' },
      },
      {
        path: 'knowledge/docs/:slug',
        name: 'KnowledgeDocDetail',
        component: () => import('@/views/knowledge/DocDetail.vue'),
        meta: { title: '文档详情', hidden: true },
      },
      {
        path: 'knowledge/interview',
        name: 'KnowledgeInterview',
        component: () => import('@/views/knowledge/Interview.vue'),
        meta: { title: '面试题库', icon: 'QuestionCircleOutlined' },
      },
      {
        path: 'resources/overview',
        name: 'ResourceOverview',
        component: () => import('@/views/resources/Overview.vue'),
        meta: { title: '资源概览' },
      },
      {
        path: 'resources/:provider',
        name: 'CloudProvider',
        component: () => import('@/views/resources/CloudProvider.vue'),
        meta: { title: '云资源管理', hidden: true },
      },
      {
        path: 'resources/:provider/:type',
        name: 'ResourceType',
        component: () => import('@/views/resources/ResourceType.vue'),
        meta: { title: '资源详情', hidden: true },
      },
      {
        path: 'resources/:id',
        name: 'ResourceDetail',
        component: () => import('@/views/resources/Detail.vue'),
        meta: { title: '资源详情', hidden: true },
      },
      {
        path: 'graph-styles',
        name: 'GraphStyles',
        component: () => import('@/views/tools/GraphStyles.vue'),
        meta: { title: '图谱样式预览', hidden: true },
      },
      {
        path: 'graph-demo',
        name: 'GraphDemo',
        component: () => import('@/views/tools/GraphDemo.vue'),
        meta: { title: '图谱交互 Demo', hidden: true },
      },
      {
        path: 'presentation',
        name: 'PresentationHub',
        component: () => import('@/views/presentation/PresentationHub.vue'),
        meta: { title: '系统演示', icon: 'PlayCircleOutlined' },
      },
      {
        path: 'presentation/:sceneId',
        name: 'PresentationPlayer',
        component: () => import('@/views/presentation/PresentationPlayer.vue'),
        meta: { title: '演示播放', hidden: true },
      },
    ],
  },
]

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes,
})

// 路由守卫：未登录跳转登录页
router.beforeEach((to, _from, next) => {
  const token = localStorage.getItem('access_token')
  if (to.path !== '/login' && !token) {
    next('/login')
  } else if (to.path === '/login' && token) {
    next('/dashboard')
  } else {
    next()
  }
})

export default router
