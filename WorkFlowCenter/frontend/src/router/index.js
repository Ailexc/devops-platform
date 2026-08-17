import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const routes = [
  {
    path: '/login',
    name: 'Login',
    component: () => import('@/views/login/LoginPage.vue'),
    meta: { requiresAuth: false }
  },
  {
    path: '/preview/flow-designer',
    name: 'FlowDesignerPreview',
    component: () => import('@/views/demo/FlowDesignerPreview.vue'),
    meta: { title: '流程设计器预览', requiresAuth: false }
  },
  {
    path: '/preview/submit-precheck',
    name: 'SubmitPrecheckPreview',
    component: () => import('@/views/demo/SubmitPrecheckPreview.vue'),
    meta: { title: '提单预检与流程预演', requiresAuth: false }
  },
  {
    path: '/',
    component: () => import('@/views/layout/AppLayout.vue'),
    meta: { requiresAuth: true },
    children: [
      // ==================== 工作台 ====================
      { path: '', redirect: '/dashboard' },
      {
        path: 'dashboard',
        name: 'Dashboard',
        component: () => import('@/views/home/HomePage.vue'),
        meta: { title: '工作台', group: 'workspace' }
      },

      // ==================== 流程办理 ====================
      {
        path: 'apply',
        name: 'Apply',
        component: () => import('@/views/process/ApplyPage.vue'),
        meta: { title: '发起申请', group: 'workflow' }
      },
      {
        path: 'my/applications',
        name: 'MyApplications',
        component: () => import('@/views/process/MyApplications.vue'),
        meta: { title: '我的申请', group: 'workflow' }
      },
      {
        path: 'my/applications/:id',
        name: 'MyApplicationDetail',
        component: () => import('@/views/process/MyApplicationDetail.vue'),
        meta: { title: '申请详情', group: 'workflow' }
      },
      {
        path: 'my/todo',
        name: 'TodoList',
        component: () => import('@/views/task/ApprovalTaskList.vue'),
        meta: { title: '待办审批', group: 'workflow', mode: 'todo' }
      },
      {
        path: 'my/done',
        name: 'DoneList',
        component: () => import('@/views/task/ApprovalTaskList.vue'),
        meta: { title: '已办审批', group: 'workflow', mode: 'done' }
      },
      {
        path: 'my/cc',
        name: 'CcList',
        component: () => import('@/views/task/ApprovalTaskList.vue'),
        meta: { title: '抄送我的', group: 'workflow', mode: 'cc' }
      },
      {
        path: 'my/tasks/:id',
        name: 'TaskDetail',
        component: () => import('@/views/task/TaskDetail.vue'),
        meta: { title: '任务办理', group: 'workflow' }
      },

      // ==================== 工单管理 ====================
      {
        path: 'tickets',
        name: 'TicketList',
        component: () => import('@/views/ticket/TicketList.vue'),
        meta: { title: '工单列表', group: 'workflow' }
      },
      {
        path: 'tickets/new',
        name: 'TicketCreate',
        component: () => import('@/views/ticket/TicketCreate.vue'),
        meta: { title: '创建工单', group: 'workflow' }
      },
      {
        path: 'tickets/:id',
        name: 'TicketDetail',
        component: () => import('@/views/ticket/TicketDetail.vue'),
        meta: { title: '工单详情', group: 'workflow' }
      },

      // ==================== 流程配置 ====================
      {
        path: 'admin/process-definitions',
        name: 'ProcessDefinitionList',
        component: () => import('@/views/process/ProcessDefinitionList.vue'),
        meta: { title: '流程配置', group: 'config' }
      },
      {
        path: 'admin/process-definitions/new',
        name: 'ProcessDefinitionNew',
        component: () => import('@/views/process/ProcessDefinitionEditor.vue'),
        meta: { title: '新建流程', group: 'config' }
      },
      {
        path: 'admin/process-definitions/:id',
        name: 'ProcessDefinitionEdit',
        component: () => import('@/views/process/ProcessDefinitionEditor.vue'),
        meta: { title: '编辑流程', group: 'config' }
      },

      // ==================== 任务平台 ====================
      {
        path: 'admin/task-jobs',
        name: 'TaskJobList',
        component: () => import('@/views/admin/TaskJobList.vue'),
        meta: { title: '任务中心', group: 'task-platform' }
      },
      {
        path: 'admin/capabilities',
        name: 'CapabilityList',
        component: () => import('@/views/admin/CapabilityList.vue'),
        meta: { title: '能力注册', group: 'task-platform' }
      },
      {
        path: 'admin/capabilities/:id',
        name: 'CapabilityDetail',
        component: () => import('@/views/admin/CapabilityDetail.vue'),
        meta: { title: '能力详情', group: 'task-platform' }
      },

      // ==================== 集成中心 ====================
      {
        path: 'admin/channels',
        name: 'MessageChannels',
        component: () => import('@/views/admin/MessageChannels.vue'),
        meta: { title: '消息通道', group: 'integration' }
      },
      {
        path: 'admin/events',
        name: 'EventLogList',
        component: () => import('@/views/admin/EventLogList.vue'),
        meta: { title: '事件日志', group: 'integration' }
      },

      // ==================== 组织权限 ====================
      {
        path: 'admin/users',
        name: 'UserList',
        component: () => import('@/views/admin/UserList.vue'),
        meta: { title: '用户管理', group: 'org' }
      },
      {
        path: 'admin/departments',
        name: 'DepartmentList',
        component: () => import('@/views/admin/DepartmentList.vue'),
        meta: { title: '部门管理', group: 'org' }
      },
      {
        path: 'admin/roles',
        name: 'RoleList',
        component: () => import('@/views/admin/RoleList.vue'),
        meta: { title: '角色管理', group: 'config' }
      },

      // ==================== 系统设置 ====================
      {
        path: 'admin/ticket-types',
        name: 'TicketTypeList',
        component: () => import('@/views/admin/TicketTypeList.vue'),
        meta: { title: '工单类型', group: 'config' }
      },
      {
        path: 'admin/initiator-apps',
        name: 'InitiatorAppList',
        component: () => import('@/views/admin/InitiatorAppList.vue'),
        meta: { title: '开放 API', group: 'integration' }
      },
      {
        path: 'admin/im-channels',
        name: 'ImChannels',
        component: () => import('@/views/admin/ImChannels.vue'),
        meta: { title: '协同渠道', group: 'integration' }
      },
      {
        path: 'notifications',
        name: 'NotificationCenter',
        component: () => import('@/views/notification/NotificationCenter.vue'),
        meta: { title: '通知中心', group: 'system' }
      },
      {
        path: 'admin/ai',
        name: 'AiConfigPage',
        component: () => import('@/views/admin/AiConfigPage.vue'),
        meta: { title: 'AI 配置', group: 'config' }
      },

      // ==================== 流程测试模块 ====================
      {
        path: 'dev/e2e-test',
        name: 'E2eTestPage',
        component: () => import('@/views/dev/E2eTestPage.vue'),
        meta: { title: '流程测试', group: 'dev' }
      },
      {
        path: 'dev/e2e-test/:key',
        name: 'E2eTestDetail',
        component: () => import('@/views/dev/E2eTestDetail.vue'),
        meta: { title: '流程测试详情', group: 'dev' }
      },

      // ==================== 系统宣讲 ====================
      {
        path: 'presentation',
        name: 'PresentationHub',
        component: () => import('@/views/presentation/PresentationHub.vue'),
        meta: { title: '系统宣讲', group: 'system' }
      },
      {
        path: 'presentation/:sceneId',
        name: 'PresentationPlayer',
        component: () => import('@/views/presentation/PresentationPlayer.vue'),
        meta: { title: '系统宣讲', group: 'system' },
        props: true,
      },

      // ==================== 系统知识库 ====================
      {
        path: 'knowledge/docs',
        name: 'KnowledgeDocs',
        component: () => import('@/views/knowledge/DocumentList.vue'),
        meta: { title: '系统文档', group: 'knowledge' }
      },
      {
        path: 'knowledge/docs/:key',
        name: 'KnowledgeDocDetail',
        component: () => import('@/views/knowledge/DocumentDetail.vue'),
        meta: { title: '文档详情', group: 'knowledge' }
      },
      {
        path: 'knowledge/interview',
        name: 'InterviewBank',
        component: () => import('@/views/knowledge/InterviewBank.vue'),
        meta: { title: '面试题库', group: 'knowledge' }
      }
    ]
  },

  // ==================== 旧路由重定向（兼容） ====================
  // 注意：vue-router 4 的字符串重定向不会替换 :id 参数，必须用函数形式
  { path: '/tickets/new', redirect: '/apply' },
  { path: '/tickets', redirect: '/my/applications' },
  { path: '/tickets/:id', redirect: (to) => `/my/applications/${to.params.id}` },
  { path: '/tasks', redirect: '/my/todo' },
  { path: '/tasks/:id', redirect: (to) => `/my/tasks/${to.params.id}` },
  { path: '/process-definitions', redirect: '/admin/process-definitions' },
  { path: '/process-definitions/new', redirect: '/admin/process-definitions/new' },
  { path: '/process-definitions/:id', redirect: (to) => `/admin/process-definitions/${to.params.id}` },
  { path: '/admin/webhooks', redirect: '/admin/channels' }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

// 路由守卫
router.beforeEach((to, from, next) => {
  const authStore = useAuthStore()

  if (to.meta.requiresAuth !== false && !authStore.isAuthenticated) {
    next({ path: '/login', query: { redirect: to.fullPath } })
  } else {
    next()
  }
})

export default router
