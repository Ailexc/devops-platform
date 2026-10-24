import { createRouter, createWebHistory } from 'vue-router'
import { api } from '../api/client'

const routes = [
  { path: '/login', component: () => import('../views/Login.vue') },
  {
    path: '/',
    component: () => import('../views/Layout.vue'),
    children: [
      // 工作台（我的首页）
      { path: '', name: 'workbench', component: () => import('../views/Workbench.vue'), meta: { title: '工作台' } },
      // 个人权限
      { path: 'me/permissions', name: 'my-permissions', component: () => import('../views/MyPermissions.vue'), meta: { title: '我的权限' } },
      { path: 'me/groups', name: 'my-groups', component: () => import('../views/MyGroups.vue'), meta: { title: '我的自建组' } },
      { path: 'requests', name: 'requests', component: () => import('../views/Requests.vue'), meta: { title: '审批中心' } },
      { path: 'requests/:id', name: 'request-detail', component: () => import('../views/RequestDetail.vue'), meta: { title: '申请单详情', crumb: [{ title: '审批中心', path: '/requests' }, { title: '申请单详情' }] } },
      // 应用权限
      { path: 'apps', name: 'apps', component: () => import('../views/Apps.vue'), meta: { title: '应用管理' } },
      { path: 'apps/register', name: 'app-register', component: () => import('../views/AppRegister.vue'), meta: { title: '注册应用', crumb: [{ title: '应用管理', path: '/apps' }, { title: '注册应用' }] } },
      { path: 'apps/:id', name: 'app-detail', component: () => import('../views/AppDetail.vue'), meta: { title: '应用详情', crumb: [{ title: '应用管理', path: '/apps' }, { title: '应用详情' }] } },
      { path: 'apps/:id/routes', name: 'route-table', component: () => import('../views/RouteTable.vue'), meta: { title: '路由表', crumb: [{ title: '应用管理', path: '/apps' }, { title: '路由表' }] } },
      { path: 'apps/:id/capabilities/:cid', name: 'capability-editor', component: () => import('../views/CapabilityEditor.vue'), meta: { title: '能力详情', crumb: [{ title: '能力管理', path: '/capabilities' }, { title: '能力详情' }] } },
      { path: 'apps/:id/capabilities/:cid/authz', name: 'capability-authz', component: () => import('../views/CapabilityAuthz.vue'), meta: { title: '授权管理', crumb: [{ title: '能力管理', path: '/capabilities' }, { title: '授权管理' }] } },
      { path: 'capabilities', name: 'capabilities', component: () => import('../views/Capabilities.vue'), meta: { title: '能力管理' } },
      { path: 'policies', name: 'policies', component: () => import('../views/Policies.vue'), meta: { title: '策略管理' } },
      { path: 'marketplace', name: 'marketplace', component: () => import('../views/Marketplace.vue'), meta: { title: '能力市场' } },
      { path: 'app-market', name: 'app-market', component: () => import('../views/AppMarket.vue'), meta: { title: '应用市场' } },
      { path: 'users', name: 'users', component: () => import('../views/Users.vue'), meta: { title: '用户管理' } },
      // 组织 / 组
      { path: 'groups', name: 'groups', component: () => import('../views/Groups.vue'), meta: { title: '组织与组' } },
      { path: 'groups/:id', name: 'group-detail', component: () => import('../views/GroupDetail.vue'), meta: { title: '组详情', crumb: [{ title: '我的自建组', path: '/me/groups' }, { title: '组详情' }] } },
      // 系统（全局只读合规入口）
      { path: 'subjects', name: 'subjects', component: () => import('../views/Subjects.vue'), meta: { title: '授权主体' } },
      { path: 'audit', name: 'audit', component: () => import('../views/Audit.vue'), meta: { title: '审计日志' } },
      // 系统观测（黑盒显性化）
      { path: 'observability/trace', name: 'obs-trace', component: () => import('../views/AuthzTrace.vue'), meta: { title: '鉴权链路追踪' } },
      { path: 'observability/resolver', name: 'obs-resolver', component: () => import('../views/ResolverWorkbench.vue'), meta: { title: 'PEP 解析工作台' } },
      { path: 'observability/pip', name: 'obs-pip', component: () => import('../views/PipExplorer.vue'), meta: { title: '身份解析（PIP）' } },
      { path: 'observability/cache', name: 'obs-cache', component: () => import('../views/ObsCache.vue'), meta: { title: '决策缓存工作台' } },
      { path: 'observability/metrics', name: 'obs-metrics', component: () => import('../views/ObsMetrics.vue'), meta: { title: '鉴权指标面板' } },
      { path: 'observability/owners', name: 'obs-owners', component: () => import('../views/ObsOwners.vue'), meta: { title: 'Owner 巡检视图' } },
      { path: 'observability/agents', name: 'obs-agents', component: () => import('../views/Agents.vue'), meta: { title: 'Agent · 分发 · 同步' } },
      // 系统知识库（复盘文档 / 面试题库）
      { path: 'knowledge/docs', name: 'knowledge-docs', component: () => import('../views/KnowledgeDocs.vue'), meta: { title: '系统文档' } },
      { path: 'knowledge/docs/:id', name: 'knowledge-doc-detail', component: () => import('../views/KnowledgeDocDetail.vue'), meta: { title: '文档详情', crumb: [{ title: '系统文档', path: '/knowledge/docs' }, { title: '文档详情' }] } },
      { path: 'knowledge/interview', name: 'knowledge-interview', component: () => import('../views/InterviewBank.vue'), meta: { title: '面试题库' } },
      { path: 'demo', name: 'demo', component: () => import('../views/DemoPlay.vue'), meta: { title: '演示模式' } },
      { path: 'demo/:slug', name: 'demo-play', component: () => import('../views/DemoPlay.vue'), meta: { title: '演示播放', crumb: [{ title: '系统演示', path: '/demo' }, { title: '演示播放' }] } },
    ],
  },
]

const router = createRouter({ history: createWebHistory(), routes })

// 网关会话模式：通过 API 调用判断登录态（Cookie 自动携带）
let _userChecked = false
let _isLoggedIn = false

router.beforeEach(async (to) => {
  // 首次访问：尝试从网关会话恢复用户
  if (!_userChecked) {
    _userChecked = true
    try {
      await api.me()
      _isLoggedIn = true
    } catch {
      _isLoggedIn = false
    }
  }
  if (to.path !== '/login' && !_isLoggedIn) {
    return '/login'
  }
})

export default router
