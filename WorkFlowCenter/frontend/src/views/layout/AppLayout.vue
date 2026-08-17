<template>
  <div class="app-layout">
    <!-- 侧边栏 -->
    <aside class="sidebar" :class="{ collapsed: isCollapse }">
      <!-- Logo -->
      <div class="sidebar-logo">
        <div class="logo-icon">
          <svg viewBox="0 0 32 32" fill="none" xmlns="http://www.w3.org/2000/svg">
            <rect width="32" height="32" rx="8" fill="url(#logo-gradient)"/>
            <path d="M8 10h16v2.5H8zM8 15h11v2.5H8zM8 20h6v2.5H8z" fill="white" fill-opacity="0.9"/>
            <circle cx="24" cy="22" r="4" fill="#4ADE80"/>
            <path d="M22.5 22l1 1 2-2" stroke="white" stroke-width="1.2" stroke-linecap="round" stroke-linejoin="round"/>
            <defs>
              <linearGradient id="logo-gradient" x1="0" y1="0" x2="32" y2="32">
                <stop stop-color="#409EFF"/>
                <stop offset="1" stop-color="#2563EB"/>
              </linearGradient>
            </defs>
          </svg>
        </div>
        <transition name="fade">
          <div v-if="!isCollapse" class="logo-text">
            <span class="logo-name">Workflow</span>
            <span class="logo-sub">流程引擎</span>
          </div>
        </transition>
      </div>

      <!-- 菜单 -->
      <nav class="sidebar-nav">
        <el-scrollbar>
          <el-menu
            :default-active="activeMenu"
            :collapse="isCollapse"
            :collapse-transition="false"
            router
            class="nav-menu"
          >
            <!-- 工作台 -->
            <el-menu-item index="/dashboard">
              <el-icon><Odometer /></el-icon>
              <template #title>工作台</template>
            </el-menu-item>

            <!-- 流程办理 -->
            <div class="nav-group">
              <div v-if="!isCollapse" class="nav-group-title">流程办理</div>
              <div v-else class="nav-group-divider"></div>
            </div>
            <el-menu-item index="/apply">
              <el-icon><Promotion /></el-icon>
              <template #title>发起申请</template>
            </el-menu-item>
            <el-menu-item index="/my/applications">
              <el-icon><Tickets /></el-icon>
              <template #title>我的申请</template>
            </el-menu-item>
            <el-menu-item index="/my/todo">
              <el-icon><AlarmClock /></el-icon>
              <template #title>待办审批 <span v-if="todoCount" class="todo-count">· {{ todoCount }}</span></template>
            </el-menu-item>
            <el-menu-item index="/my/done">
              <el-icon><Finished /></el-icon>
              <template #title>已办审批</template>
            </el-menu-item>
            <el-menu-item index="/my/cc">
              <el-icon><Message /></el-icon>
              <template #title>抄送我的</template>
            </el-menu-item>

            <!-- 管理员菜单 -->
            <template v-if="isAdmin">
              <div class="nav-group">
                <div v-if="!isCollapse" class="nav-group-title">流程管理</div>
                <div v-else class="nav-group-divider"></div>
              </div>
              <el-menu-item index="/admin/process-definitions">
                <el-icon><Setting /></el-icon>
                <template #title>流程配置</template>
              </el-menu-item>
              <el-menu-item index="/admin/roles">
                <el-icon><Avatar /></el-icon>
                <template #title>角色管理</template>
              </el-menu-item>
              <el-menu-item index="/admin/ticket-types">
                <el-icon><Collection /></el-icon>
                <template #title>工单类型</template>
              </el-menu-item>
              <el-menu-item index="/admin/ai">
                <el-icon><MagicStick /></el-icon>
                <template #title>AI 配置</template>
              </el-menu-item>

              <div class="nav-group">
                <div v-if="!isCollapse" class="nav-group-title">任务平台</div>
                <div v-else class="nav-group-divider"></div>
              </div>
              <el-menu-item index="/admin/task-jobs">
                <el-icon><DataAnalysis /></el-icon>
                <template #title>任务中心</template>
              </el-menu-item>
              <el-menu-item index="/admin/capabilities">
                <el-icon><Connection /></el-icon>
                <template #title>能力注册</template>
              </el-menu-item>

              <div class="nav-group">
                <div v-if="!isCollapse" class="nav-group-title">集成</div>
                <div v-else class="nav-group-divider"></div>
              </div>
              <el-menu-item index="/admin/initiator-apps">
                <el-icon><Link /></el-icon>
                <template #title>开放 API</template>
              </el-menu-item>
              <el-menu-item index="/admin/channels">
                <el-icon><Connection /></el-icon>
                <template #title>消息通道</template>
              </el-menu-item>
              <el-menu-item index="/admin/im-channels">
                <el-icon><ChatDotRound /></el-icon>
                <template #title>协同渠道</template>
              </el-menu-item>
              <el-menu-item index="/admin/events">
                <el-icon><List /></el-icon>
                <template #title>事件日志</template>
              </el-menu-item>

              <div class="nav-group">
                <div v-if="!isCollapse" class="nav-group-title">组织</div>
                <div v-else class="nav-group-divider"></div>
              </div>
              <el-menu-item index="/admin/users">
                <el-icon><User /></el-icon>
                <template #title>用户管理</template>
              </el-menu-item>
              <el-menu-item index="/admin/departments">
                <el-icon><OfficeBuilding /></el-icon>
                <template #title>部门管理</template>
              </el-menu-item>

              <div class="nav-group">
                <div v-if="!isCollapse" class="nav-group-title">演示</div>
                <div v-else class="nav-group-divider"></div>
              </div>
              <el-menu-item index="/dev/e2e-test">
                <el-icon><Aim /></el-icon>
                <template #title>流程测试</template>
              </el-menu-item>
              <el-menu-item index="/presentation">
                <el-icon><Monitor /></el-icon>
                <template #title>系统宣讲</template>
              </el-menu-item>
            </template>

            <!-- 系统知识库 -->
            <div class="nav-group">
              <div v-if="!isCollapse" class="nav-group-title">系统知识库</div>
              <div v-else class="nav-group-divider"></div>
            </div>
            <el-menu-item index="/knowledge/docs">
              <el-icon><Reading /></el-icon>
              <template #title>系统文档</template>
            </el-menu-item>
            <el-menu-item index="/knowledge/interview">
              <el-icon><QuestionFilled /></el-icon>
              <template #title>面试题库</template>
            </el-menu-item>
          </el-menu>
        </el-scrollbar>
      </nav>

      <!-- 底部折叠按钮 -->
      <div class="sidebar-footer">
        <div class="collapse-trigger" @click="isCollapse = !isCollapse">
          <el-icon :size="18">
            <Fold v-if="!isCollapse" />
            <Expand v-else />
          </el-icon>
          <transition name="fade">
            <span v-if="!isCollapse" class="collapse-text">收起菜单</span>
          </transition>
        </div>
      </div>
    </aside>

    <!-- 主内容区 -->
    <div class="main-wrapper">
      <!-- 顶部栏 -->
      <header class="topbar">
        <div class="topbar-left">
          <el-breadcrumb separator="/">
            <el-breadcrumb-item :to="{ path: '/dashboard' }">首页</el-breadcrumb-item>
            <el-breadcrumb-item v-if="currentRoute.meta.title">
              {{ currentRoute.meta.title }}
            </el-breadcrumb-item>
          </el-breadcrumb>
        </div>

        <div class="topbar-right">
          <!-- 用户菜单 -->
          <el-dropdown @command="handleCommand" trigger="click">
            <div class="user-chip">
              <div class="user-avatar">{{ userInitial }}</div>
              <div class="user-meta">
                <span class="user-name">{{ authStore.user?.username || '用户' }}</span>
                <span class="user-role">{{ isAdmin ? '管理员' : '普通用户' }}</span>
              </div>
              <el-icon class="user-arrow"><ArrowDown /></el-icon>
            </div>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item command="profile">
                  <el-icon><User /></el-icon> 个人中心
                </el-dropdown-item>
                <el-dropdown-item divided command="logout">
                  <el-icon><SwitchButton /></el-icon> 退出登录
                </el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </div>
      </header>

      <!-- 内容区域 -->
      <main class="app-main">
        <router-view />
      </main>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onBeforeUnmount } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import {
  Odometer, Document, Promotion, Tickets, AlarmClock,
  Finished, Message, Setting, Cpu, DataAnalysis, Connection, Link, List, ChatDotRound,
  User, OfficeBuilding, Avatar, Collection, MagicStick,
  Fold, Expand, ArrowDown, SwitchButton, Aim, Reading, QuestionFilled
} from '@element-plus/icons-vue'
import { ElMessageBox } from 'element-plus'
import { getTasks } from '@/api/modules/task'

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()

const isCollapse = ref(false)
const todoCount = ref(0)
let refreshTimer = null

const currentRoute = computed(() => route)
const activeMenu = computed(() => route.path)
const isAdmin = computed(() => authStore.user?.is_staff)

const userInitial = computed(() => {
  const username = authStore.user?.username || 'U'
  return username.charAt(0).toUpperCase()
})

const fetchTodoCount = async () => {
  try {
    const response = await getTasks({ type: 'todo', page_size: 1 })
    const data = response?.data ?? response
    todoCount.value = data?.count ?? 0
  } catch (error) {
    // 静默失败
  }
}

const handleCommand = (command) => {
  switch (command) {
    case 'profile':
      break
    case 'logout':
      ElMessageBox.confirm('确定要退出登录吗？', '提示', {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }).then(() => {
        authStore.logout()
      }).catch(() => {})
      break
  }
}

onMounted(() => {
  fetchTodoCount()
  refreshTimer = setInterval(fetchTodoCount, 60000)
})

onBeforeUnmount(() => {
  if (refreshTimer) clearInterval(refreshTimer)
})
</script>

<style scoped>
/* ============================================================
   现代布局系统
   ============================================================ */
.app-layout {
  display: flex;
  height: 100vh;
  overflow: hidden;
  background: #F7F8FA;
}

/* ===================== 侧边栏 ===================== */
.sidebar {
  width: 240px;
  background: #FFFFFF;
  border-right: 1px solid #F2F3F5;
  display: flex;
  flex-direction: column;
  transition: width 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  position: relative;
  z-index: 100;
  flex-shrink: 0;
}
.sidebar.collapsed {
  width: 64px;
}

/* Logo */
.sidebar-logo {
  height: 64px;
  display: flex;
  align-items: center;
  padding: 0 16px;
  gap: 12px;
  border-bottom: 1px solid #F2F3F5;
  flex-shrink: 0;
}
.logo-icon svg {
  width: 32px;
  height: 32px;
  flex-shrink: 0;
}
.logo-text {
  display: flex;
  flex-direction: column;
  min-width: 0;
  white-space: nowrap;
}
.logo-name {
  font-size: 16px;
  font-weight: 700;
  color: #303133;
  letter-spacing: -0.3px;
  line-height: 1.2;
}
.logo-sub {
  font-size: 11px;
  color: #86909C;
  letter-spacing: 0.5px;
}

/* 菜单导航 */
.sidebar-nav {
  flex: 1;
  overflow: hidden;
  padding: 8px 0;
}
.nav-menu {
  border: none !important;
  background: transparent !important;
  padding: 0 8px;
}
.nav-group {
  padding: 16px 12px 6px;
}
.nav-group-title {
  font-size: 11px;
  font-weight: 600;
  color: #C0C4CC;
  text-transform: uppercase;
  letter-spacing: 0.8px;
}
.nav-group-divider {
  width: 16px;
  height: 1px;
  background: #F2F3F5;
  margin: 12px auto 4px;
}

/* Element Plus 菜单覆盖 */
:deep(.el-menu) {
  background: transparent !important;
}
:deep(.el-menu-item) {
  height: 40px;
  line-height: 40px;
  margin: 2px 0;
  padding-left: 12px !important;
  border-radius: 8px;
  color: #606266 !important;
  font-size: 13px;
  font-weight: 500;
  transition: all 0.2s;
}
:deep(.el-menu-item:hover) {
  background: #F5F7FA !important;
  color: #409EFF !important;
}
:deep(.el-menu-item.is-active) {
  background: #EBF5FF !important;
  color: #409EFF !important;
  font-weight: 600;
}
:deep(.el-menu-item.is-active::before) {
  content: '';
  position: absolute;
  left: 0;
  top: 8px;
  bottom: 8px;
  width: 3px;
  border-radius: 0 3px 3px 0;
  background: #409EFF;
}
:deep(.el-menu-item .el-icon) {
  font-size: 18px;
  margin-right: 10px;
  width: 18px;
}

.todo-count {
  font-size: 12px;
  font-weight: 700;
  color: #E6A23C;
  margin-left: 6px;
}
:deep(.el-sub-menu .el-sub-menu__title) {
  color: #606266 !important;
  height: 40px;
  line-height: 40px;
  border-radius: 8px;
  font-size: 13px;
  font-weight: 500;
}
:deep(.el-sub-menu .el-sub-menu__title:hover) {
  background: #F5F7FA !important;
  color: #409EFF !important;
}
:deep(.el-menu--collapse .el-menu-item) {
  padding-left: 0 !important;
  justify-content: center;
}
:deep(.el-menu--collapse .el-menu-item .el-icon) {
  margin-right: 0;
}

/* 侧边栏底部 */
.sidebar-footer {
  border-top: 1px solid #F2F3F5;
  padding: 8px;
  flex-shrink: 0;
}
.collapse-trigger {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  height: 36px;
  border-radius: 8px;
  cursor: pointer;
  color: #606266;
  transition: all 0.2s;
}
.collapse-trigger:hover {
  background: #F5F7FA;
  color: #409EFF;
}
.collapse-text {
  font-size: 12px;
  white-space: nowrap;
}

/* ===================== 主内容区 ===================== */
.main-wrapper {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  min-width: 0;
}

/* 顶部栏 */
.topbar {
  height: 56px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 24px;
  background: #fff;
  border-bottom: 1px solid #F2F3F5;
  flex-shrink: 0;
  z-index: 10;
}
.topbar-left {
  display: flex;
  align-items: center;
}
.topbar-right {
  display: flex;
  align-items: center;
  gap: 8px;
}

/* 通知按钮 */
.topbar-icon-btn {
  width: 36px;
  height: 36px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  color: #86909C;
  transition: all 0.2s;
}
.topbar-icon-btn:hover {
  background: #F7F8FA;
  color: #409EFF;
}

/* 用户信息卡片 */
.user-chip {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 4px 8px 4px 4px;
  border-radius: 10px;
  cursor: pointer;
  transition: background 0.2s;
}
.user-chip:hover {
  background: #F7F8FA;
}
.user-avatar {
  width: 32px;
  height: 32px;
  border-radius: 8px;
  background: linear-gradient(135deg, #409EFF, #2563EB);
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 13px;
  font-weight: 700;
}
.user-meta {
  display: flex;
  flex-direction: column;
  line-height: 1.3;
}
.user-name {
  font-size: 13px;
  font-weight: 600;
  color: #1D2129;
}
.user-role {
  font-size: 11px;
  color: #86909C;
}
.user-arrow {
  font-size: 12px;
  color: #C9CDD4;
  margin-left: 2px;
}

/* 内容区域 */
.app-main {
  flex: 1;
  overflow-y: auto;
  background: #F7F8FA;
}

/* ===================== 过渡动画 ===================== */
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.2s;
}
.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
.page-fade-enter-active {
  transition: opacity 0.2s ease-out;
}
.page-fade-leave-active {
  transition: opacity 0.15s ease-in;
}
.page-fade-enter-from,
.page-fade-leave-to {
  opacity: 0;
}

/* ===================== 响应式 ===================== */
@media (max-width: 768px) {
  .sidebar {
    position: fixed;
    left: 0;
    top: 0;
    bottom: 0;
    z-index: 1000;
    transform: translateX(-100%);
    transition: transform 0.3s;
  }
  .sidebar:not(.collapsed) {
    transform: translateX(0);
  }
}
</style>
