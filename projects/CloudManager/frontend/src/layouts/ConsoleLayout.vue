<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useUserStore } from '@/stores/user'
import { useTabStore } from '@/stores/tabs'

const router = useRouter()
const route = useRoute()
const userStore = useUserStore()
const tabStore = useTabStore()

const collapsed = ref(false)
const showUserMenu = ref(false)

// 菜单项类型定义
type MenuItem = {
  key: string
  label: string
  icon: string
  children?: { key: string; label: string }[]
}

// 菜单项配置 - 一级菜单可折叠，二级菜单为具体页面
const menuGroups: { title: string; items: MenuItem[] }[] = [
  {
    title: '概览',
    items: [
      {
        key: '/dashboard',
        label: '工作台',
        icon: 'dashboard',
      },
    ],
  },
  {
    title: '资源管理',
    items: [
      {
        key: 'resources',
        label: '资源管理',
        icon: 'cloud',
        children: [
          { key: '/resources/overview', label: '资源概览' },
          { key: '/resources/aws', label: 'AWS' },
          { key: '/resources/aliyun', label: '阿里云' },
          { key: '/resources/tencent', label: '腾讯云' },
          { key: '/cloud-accounts', label: '云账号管理' },
        ],
      },
    ],
  },
  {
    title: '业务中心',
    items: [
      {
        key: '/applications',
        label: '应用中心',
        icon: 'grid',
      },
    ],
  },
  {
    title: '运维中心',
    items: [
      {
        key: '/ticket/list',
        label: '工单中心',
        icon: 'file-text',
      },
      {
        key: '/scenarios',
        label: '场景模板库',
        icon: 'thunder',
      },
      {
        key: '/audit/logs',
        label: '操作记录',
        icon: 'audit',
      },
    ],
  },
  {
    title: '财务管理',
    items: [
      {
        key: 'cost',
        label: '成本管理',
        icon: 'dollar',
        children: [
          { key: '/cost/trends', label: '成本趋势' },
          { key: '/cost/overview', label: '成本优化总览' },
          { key: '/cost/rules', label: '规则配置' },
          { key: '/cost/reports', label: '分析报告' },
        ],
      },
    ],
  },
  {
    title: '系统演示',
    items: [
      {
        key: '/presentation',
        label: '🎬 系统演示',
        icon: 'play',
      },
    ],
  },
  {
    title: '系统知识库',
    items: [
      {
        key: 'knowledge',
        label: '系统知识库',
        icon: 'book',
        children: [
          { key: '/knowledge/docs', label: '系统文档' },
          { key: '/knowledge/interview', label: '面试题库' },
        ],
      },
    ],
  },
]

// 图标映射
const icons: Record<string, string> = {
  dashboard: 'M4 5a1 1 0 0 1 1-1h4a1 1 0 0 1 1 1v4a1 1 0 0 1-1 1H5a1 1 0 0 1-1-1V5zm10 0a1 1 0 0 1 1-1h4a1 1 0 0 1 1 1v4a1 1 0 0 1-1 1h-4a1 1 0 0 1-1-1V5zM4 15a1 1 0 0 1 1-1h4a1 1 0 0 1 1 1v4a1 1 0 0 1-1 1H5a1 1 0 0 1-1-1v-4zm10 0a1 1 0 0 1 1-1h4a1 1 0 0 1 1 1v4a1 1 0 0 1-1 1h-4a1 1 0 0 1-1-1v-4z',
  server: 'M5 3a2 2 0 0 0-2 2v2a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2V5a2 2 0 0 0-2-2H5zm0 6a2 2 0 0 0-2 2v2a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-2a2 2 0 0 0-2-2H5zm0 6a2 2 0 0 0-2 2v2a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-2a2 2 0 0 0-2-2H5z',
  grid: 'M3 3h8v8H3V3zm10 0h8v8h-8V3zM3 13h8v8H3v-8zm10 0h8v8h-8v-8z',
  'file-text': 'M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8l-6-6zm4 18H6V4h7v5h5v11zM8 15h8M8 11h4',
  audit: 'M9 5H7a2 2 0 0 0-2 2v12a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2V7a2 2 0 0 0-2-2h-2M9 5a2 2 0 0 1 2-2h2a2 2 0 0 1 2 2M9 5h6m-6 4h6m-6 4h4m-4 4h2',
  dollar: 'M12 2v20m5-17H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H7',
  thunder: 'M13 2L3 14h9l-1 8 10-12h-9l1-8z',
  play: 'M14.752 11.168l-3.197-2.132A1 1 0 0010 9.87v4.263a1 1 0 001.555.832l3.197-2.132a1 1 0 000-1.664zM21 12a9 9 0 11-18 0 9 9 0 0118 0z',
  cloud: 'M18 10h-1.26A8 8 0 1 0 9 20h9a5 5 0 0 0 0-10z',
  book: 'M4 4a2 2 0 0 1 2-2h12a2 2 0 0 1 2 2v16a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V4zm2 0v16h12V4H6zm2 3h8M6 11h8M6 15h4',
  chart: 'M18 20V10M12 20V4M6 20v-6',
  setting: 'M12 15a3 3 0 100-6 3 3 0 000 6z M19.4 15a1.65 1.65 0 00.33 1.82l.06.06a2 2 0 010 2.83 2 2 0 01-2.83 0l-.06-.06a1.65 1.65 0 00-1.82-.33 1.65 1.65 0 00-1 1.51V21a2 2 0 01-2 2 2 2 0 01-2-2v-.09A1.65 1.65 0 009 19.4a1.65 1.65 0 00-1.82.33l-.06.06a2 2 0 01-2.83 0 2 2 0 010-2.83l.06-.06a1.65 1.65 0 00.33-1.82 1.65 1.65 0 00-1.51-1H3a2 2 0 01-2-2 2 2 0 012-2h.09A1.65 1.65 0 004.6 9a1.65 1.65 0 00-.33-1.82l-.06-.06a2 2 0 010-2.83 2 2 0 012.83 0l.06.06a1.65 1.65 0 001.82.33H9a1.65 1.65 0 001-1.51V3a2 2 0 012-2 2 2 0 012 2v.09a1.65 1.65 0 001 1.51 1.65 1.65 0 001.82-.33l.06-.06a2 2 0 012.83 0 2 2 0 010 2.83l-.06.06a1.65 1.65 0 00-.33 1.82V9a1.65 1.65 0 001.51 1H21a2 2 0 012 2 2 2 0 01-2 2h-.09a1.65 1.65 0 00-1.51 1z',
}

const selectedKeys = ref<string[]>([route.path])
const openKeys = ref<string[]>([])

// 同步路由
watch(() => route.path, (path) => {
  selectedKeys.value = [path]
  // 自动展开父菜单
  menuGroups.forEach(group => {
    group.items.forEach(item => {
      if (item.children) {
        const hasActiveChild = item.children.some(child => path.startsWith(child.key))
        if (hasActiveChild && !openKeys.value.includes(item.key)) {
          openKeys.value.push(item.key)
        }
      }
    })
  })
}, { immediate: true })

function handleMenuClick(path: string) {
  router.push(path)
}

function handleLogout() {
  userStore.logout()
  router.push('/login')
}

const displayName = computed(() => userStore.user?.display_name || userStore.user?.username || '用户')
</script>

<template>
  <div class="layout">
    <!-- 侧边栏 -->
    <aside class="sidebar" :class="{ collapsed }">
      <!-- Logo -->
      <div class="sidebar-logo">
        <div class="logo-icon">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M18 10h-1.26A8 8 0 1 0 9 20h9a5 5 0 0 0 0-10z"></path>
          </svg>
        </div>
        <transition name="fade">
          <span v-show="!collapsed" class="logo-text">Cloud Manager</span>
        </transition>
      </div>

      <!-- 导航菜单 -->
      <nav class="sidebar-nav">
        <div v-for="group in menuGroups" :key="group.title" class="nav-group">
          <transition name="fade">
            <span v-show="!collapsed" class="nav-group-title">{{ group.title }}</span>
          </transition>
          
          <div v-for="item in group.items" :key="item.key" class="nav-item-wrapper">
            <!-- 有子菜单 -->
            <div v-if="item.children" class="nav-item-group">
              <button
                class="nav-item"
                :class="{ 
                  active: openKeys.includes(item.key),
                  'justify-center': collapsed 
                }"
                @click="!collapsed && (openKeys.includes(item.key) ? openKeys = openKeys.filter(k => k !== item.key) : openKeys.push(item.key))"
              >
                <svg class="nav-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <path :d="icons[item.icon]"></path>
                </svg>
                <transition name="fade">
                  <span v-show="!collapsed" class="nav-label">{{ item.label }}</span>
                </transition>
                <svg v-show="!collapsed" class="nav-arrow" :class="{ expanded: openKeys.includes(item.key) }" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <path d="M9 18l6-6-6-6"></path>
                </svg>
              </button>
              
              <!-- 子菜单 -->
              <transition name="slide">
                <div v-show="openKeys.includes(item.key) && !collapsed" class="nav-children">
                  <button
                    v-for="child in item.children"
                    :key="child.key"
                    class="nav-child-item"
                    :class="{ active: selectedKeys.includes(child.key) }"
                    @click="handleMenuClick(child.key)"
                  >
                    <span class="child-dot"></span>
                    <span>{{ child.label }}</span>
                  </button>
                </div>
              </transition>
            </div>
            
            <!-- 无子菜单 -->
            <button
              v-else
              class="nav-item"
              :class="{ 
                active: selectedKeys.includes(item.key),
                'justify-center': collapsed 
              }"
              @click="handleMenuClick(item.key)"
            >
              <svg class="nav-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path :d="icons[item.icon]"></path>
              </svg>
              <transition name="fade">
                <span v-show="!collapsed" class="nav-label">{{ item.label }}</span>
              </transition>
            </button>
          </div>
        </div>
      </nav>

      <!-- 折叠按钮 -->
      <button class="collapse-btn" @click="collapsed = !collapsed">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" :class="{ rotated: collapsed }">
          <path d="M15 18l-6-6 6-6"></path>
        </svg>
      </button>
    </aside>

    <!-- 主内容区 -->
    <div class="main-area" :class="{ 'sidebar-collapsed': collapsed }">
      <!-- 顶部栏 -->
      <header class="header">
        <div class="header-left">
          <!-- 面包屑 -->
          <div class="breadcrumb">
            <svg class="breadcrumb-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"></path>
              <polyline points="9 22 9 12 15 12 15 22"></polyline>
            </svg>
            <span class="breadcrumb-item">首页</span>
            <span v-if="route.meta?.title" class="breadcrumb-separator">/</span>
            <span v-if="route.meta?.title" class="breadcrumb-item active">{{ route.meta.title }}</span>
          </div>
        </div>

        <div class="header-right">
          <!-- 通知 -->
          <button class="header-btn">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9"></path>
              <path d="M13.73 21a2 2 0 0 1-3.46 0"></path>
            </svg>
            <span class="notification-badge">3</span>
          </button>

          <!-- 用户菜单 -->
          <div class="user-menu" @click="showUserMenu = !showUserMenu">
            <div class="user-avatar">
              {{ displayName[0] }}
            </div>
            <span class="user-name">{{ displayName }}</span>
            <svg class="user-arrow" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M6 9l6 6 6-6"></path>
            </svg>
            
            <!-- 下拉菜单 -->
            <transition name="dropdown">
              <div v-show="showUserMenu" class="user-dropdown">
                <button class="dropdown-item">
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"></path>
                    <circle cx="12" cy="7" r="4"></circle>
                  </svg>
                  <span>个人中心</span>
                </button>
                <div class="dropdown-divider"></div>
                <button class="dropdown-item danger" @click="handleLogout">
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"></path>
                    <polyline points="16 17 21 12 16 7"></polyline>
                    <line x1="21" y1="12" x2="9" y2="12"></line>
                  </svg>
                  <span>退出登录</span>
                </button>
              </div>
            </transition>
          </div>
        </div>
      </header>

      <!-- 页签栏 -->
      <div class="tabs-bar">
        <div class="tabs-container">
          <button
            v-for="tab in tabStore.tabs"
            :key="tab.path"
            class="tab-item"
            :class="{ active: tabStore.activeTab === tab.path }"
            @click="router.push(tab.path)"
          >
            <span>{{ tab.title }}</span>
            <svg
              v-if="tab.closable"
              class="tab-close"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              stroke-width="2"
              @click.stop="tabStore.removeTab(tab.path)"
            >
              <path d="M18 6L6 18M6 6l12 12"></path>
            </svg>
          </button>
        </div>
      </div>

      <!-- 内容区 -->
      <main class="content">
        <router-view v-slot="{ Component }">
          <keep-alive>
            <component :is="Component" />
          </keep-alive>
        </router-view>
      </main>
    </div>
  </div>
</template>

<style scoped>
/* 整体布局 */
.layout {
  display: flex;
  min-height: 100vh;
  background: var(--cm-bg-primary);
}

/* 侧边栏 */
.sidebar {
  width: var(--cm-sidebar-width);
  background: #ffffff;
  display: flex;
  flex-direction: column;
  position: fixed;
  left: 0;
  top: 0;
  bottom: 0;
  z-index: 100;
  transition: width var(--cm-transition-base);
  border-right: 1px solid #e5e7eb;
}

.sidebar.collapsed {
  width: var(--cm-sidebar-collapsed-width);
}

/* Logo */
.sidebar-logo {
  height: 72px;
  display: flex;
  align-items: center;
  padding: 0 20px;
  gap: 12px;
  border-bottom: 1px solid #e5e7eb;
}

.logo-icon {
  width: 40px;
  height: 40px;
  background: linear-gradient(135deg, var(--cm-color-primary-400) 0%, var(--cm-color-primary-600) 100%);
  border-radius: var(--cm-radius-lg);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.logo-icon svg {
  width: 24px;
  height: 24px;
  color: white;
}

.logo-text {
  font-size: var(--cm-text-lg);
  font-weight: var(--cm-font-bold);
  color: #1a1a2e;
  white-space: nowrap;
}

/* 导航 */
.sidebar-nav {
  flex: 1;
  overflow-y: auto;
  padding: 16px 12px;
}

.nav-group {
  margin-bottom: 24px;
}

.nav-group-title {
  display: block;
  padding: 0 12px;
  margin-bottom: 8px;
  font-size: var(--cm-text-xs);
  font-weight: var(--cm-font-semibold);
  color: #9ca3af;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.nav-item-wrapper {
  margin-bottom: 4px;
}

.nav-item {
  width: 100%;
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 10px 12px;
  background: transparent;
  border: none;
  border-radius: var(--cm-radius-md);
  color: #4b5563;
  font-size: var(--cm-text-sm);
  font-family: inherit;
  cursor: pointer;
  transition: all var(--cm-transition-fast);
  text-align: left;
}

.nav-item:hover {
  background: #f3f4f6;
  color: #1a1a2e;
}

.nav-item.active {
  background: #eef2ff;
  color: #667eea;
}

.nav-item.justify-center {
  justify-content: center;
  padding: 10px;
}

.nav-icon {
  width: 20px;
  height: 20px;
  flex-shrink: 0;
}

.nav-label {
  flex: 1;
  white-space: nowrap;
}

.nav-arrow {
  width: 16px;
  height: 16px;
  transition: transform var(--cm-transition-fast);
  color: #9ca3af;
}

.nav-arrow.expanded {
  transform: rotate(90deg);
}

/* 子菜单 */
.nav-children {
  padding-left: 44px;
  margin-top: 4px;
}

.nav-child-item {
  width: 100%;
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  background: transparent;
  border: none;
  border-radius: var(--cm-radius-sm);
  color: #6b7280;
  font-size: var(--cm-text-sm);
  font-family: inherit;
  cursor: pointer;
  transition: all var(--cm-transition-fast);
  text-align: left;
}

.nav-child-item:hover {
  background: #f3f4f6;
  color: #1a1a2e;
}

.nav-child-item.active {
  color: #667eea;
  background: #eef2ff;
}

.child-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: #d1d5db;
  transition: all var(--cm-transition-fast);
}

.nav-child-item:hover .child-dot {
  background: #9ca3af;
}

.nav-child-item.active .child-dot {
  background: #667eea;
}

/* 折叠按钮 */
.collapse-btn {
  width: 100%;
  height: 56px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: transparent;
  border: none;
  border-top: 1px solid #e5e7eb;
  color: #9ca3af;
  cursor: pointer;
  transition: all var(--cm-transition-fast);
}

.collapse-btn:hover {
  background: #f3f4f6;
  color: #4b5563;
}

.collapse-btn svg {
  width: 20px;
  height: 20px;
  transition: transform var(--cm-transition-base);
}

.collapse-btn svg.rotated {
  transform: rotate(180deg);
}

/* 主内容区 */
.main-area {
  flex: 1;
  margin-left: var(--cm-sidebar-width);
  display: flex;
  flex-direction: column;
  min-height: 100vh;
  transition: margin-left var(--cm-transition-base);
}

.main-area.sidebar-collapsed {
  margin-left: var(--cm-sidebar-collapsed-width);
}

/* 顶部栏 */
.header {
  height: var(--cm-header-height);
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 24px;
  background: var(--cm-glass-bg);
  backdrop-filter: var(--cm-glass-blur);
  -webkit-backdrop-filter: var(--cm-glass-blur);
  border-bottom: 1px solid var(--cm-border-default);
  position: sticky;
  top: 0;
  z-index: 50;
}

.header-left {
  display: flex;
  align-items: center;
}

.header-right {
  display: flex;
  align-items: center;
  gap: 16px;
}

.header-switchers {
  display: flex;
  align-items: center;
  gap: 8px;
}

/* 面包屑 */
.breadcrumb {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: var(--cm-text-sm);
  color: var(--cm-text-secondary);
}

.breadcrumb-icon {
  width: 18px;
  height: 18px;
}

.breadcrumb-item.active {
  color: var(--cm-text-primary);
  font-weight: var(--cm-font-medium);
}

.breadcrumb-separator {
  color: var(--cm-color-gray-300);
}

/* 搜索框 */
.search-box {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  background: var(--cm-bg-tertiary);
  border: 1px solid var(--cm-border-default);
  border-radius: var(--cm-radius-md);
  transition: all var(--cm-transition-fast);
}

.search-box:focus-within {
  border-color: var(--cm-border-focus);
  box-shadow: 0 0 0 3px rgba(139, 92, 246, 0.1);
}

.search-icon {
  width: 16px;
  height: 16px;
  color: var(--cm-text-tertiary);
}

.search-input {
  width: 160px;
  background: transparent;
  border: none;
  outline: none;
  font-size: var(--cm-text-sm);
  font-family: inherit;
  color: var(--cm-text-primary);
}

.search-input::placeholder {
  color: var(--cm-text-tertiary);
}

.search-shortcut {
  padding: 2px 6px;
  background: white;
  border: 1px solid var(--cm-border-default);
  border-radius: 4px;
  font-size: 11px;
  font-family: inherit;
  color: var(--cm-text-tertiary);
}

/* 顶部按钮 */
.header-btn {
  position: relative;
  width: 40px;
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: transparent;
  border: none;
  border-radius: var(--cm-radius-md);
  color: var(--cm-text-secondary);
  cursor: pointer;
  transition: all var(--cm-transition-fast);
}

.header-btn:hover {
  background: var(--cm-bg-tertiary);
  color: var(--cm-text-primary);
}

.header-btn svg {
  width: 20px;
  height: 20px;
}

.notification-badge {
  position: absolute;
  top: 6px;
  right: 6px;
  min-width: 18px;
  height: 18px;
  padding: 0 5px;
  background: var(--cm-color-error);
  border-radius: var(--cm-radius-full);
  font-size: 11px;
  font-weight: var(--cm-font-semibold);
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
}

/* 用户菜单 */
.user-menu {
  position: relative;
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 6px 12px;
  background: transparent;
  border: 1px solid transparent;
  border-radius: var(--cm-radius-md);
  cursor: pointer;
  transition: all var(--cm-transition-fast);
}

.user-menu:hover {
  background: var(--cm-bg-tertiary);
  border-color: var(--cm-border-default);
}

.user-avatar {
  width: 32px;
  height: 32px;
  background: linear-gradient(135deg, var(--cm-color-primary-500) 0%, var(--cm-color-primary-700) 100%);
  border-radius: var(--cm-radius-full);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: var(--cm-text-sm);
  font-weight: var(--cm-font-semibold);
  color: white;
}

.user-name {
  font-size: var(--cm-text-sm);
  font-weight: var(--cm-font-medium);
  color: var(--cm-text-primary);
}

.user-arrow {
  width: 16px;
  height: 16px;
  color: var(--cm-text-tertiary);
}

/* 下拉菜单 */
.user-dropdown {
  position: absolute;
  top: calc(100% + 8px);
  right: 0;
  width: 180px;
  background: white;
  border: 1px solid var(--cm-border-default);
  border-radius: var(--cm-radius-lg);
  box-shadow: var(--cm-shadow-xl);
  padding: 8px;
  z-index: 1000;
}

.dropdown-item {
  width: 100%;
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 12px;
  background: transparent;
  border: none;
  border-radius: var(--cm-radius-md);
  font-size: var(--cm-text-sm);
  font-family: inherit;
  color: var(--cm-text-primary);
  cursor: pointer;
  transition: all var(--cm-transition-fast);
  text-align: left;
}

.dropdown-item:hover {
  background: var(--cm-bg-tertiary);
}

.dropdown-item svg {
  width: 18px;
  height: 18px;
  color: var(--cm-text-secondary);
}

.dropdown-item.danger {
  color: var(--cm-color-error);
}

.dropdown-item.danger svg {
  color: var(--cm-color-error);
}

.dropdown-divider {
  height: 1px;
  background: var(--cm-border-default);
  margin: 8px 0;
}

/* 页签栏 */
.tabs-bar {
  background: white;
  border-bottom: 1px solid var(--cm-border-default);
  padding: 0 16px;
}

.tabs-container {
  display: flex;
  gap: 4px;
  overflow-x: auto;
  scrollbar-width: none;
}

.tabs-container::-webkit-scrollbar {
  display: none;
}

.tab-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 16px;
  background: transparent;
  border: none;
  border-bottom: 2px solid transparent;
  font-size: var(--cm-text-sm);
  font-family: inherit;
  color: var(--cm-text-secondary);
  cursor: pointer;
  transition: all var(--cm-transition-fast);
  white-space: nowrap;
}

.tab-item:hover {
  color: var(--cm-text-primary);
  background: var(--cm-bg-tertiary);
}

.tab-item.active {
  color: var(--cm-color-primary-600);
  border-bottom-color: var(--cm-color-primary-600);
  font-weight: var(--cm-font-medium);
}

.tab-close {
  width: 14px;
  height: 14px;
  padding: 2px;
  border-radius: var(--cm-radius-sm);
  transition: all var(--cm-transition-fast);
}

.tab-close:hover {
  background: var(--cm-color-gray-200);
  color: var(--cm-color-gray-600);
}

/* 内容区 */
.content {
  flex: 1;
  padding: 24px;
  background: var(--cm-bg-primary);
}

/* 过渡动画 */
.fade-enter-active,
.fade-leave-active {
  transition: opacity var(--cm-transition-fast);
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}

.slide-enter-active,
.slide-leave-active {
  transition: all var(--cm-transition-base);
  overflow: hidden;
}

.slide-enter-from,
.slide-leave-to {
  opacity: 0;
  max-height: 0;
}

.slide-enter-to,
.slide-leave-from {
  opacity: 1;
  max-height: 500px;
}

.page-enter-active,
.page-leave-active {
  transition: all var(--cm-transition-base);
}

.page-enter-from {
  opacity: 0;
  transform: translateY(10px);
}

.page-leave-to {
  opacity: 0;
  transform: translateY(-10px);
}

.dropdown-enter-active,
.dropdown-leave-active {
  transition: all var(--cm-transition-fast);
}

.dropdown-enter-from,
.dropdown-leave-to {
  opacity: 0;
  transform: translateY(-8px);
}

/* 暗色模式 */
@media (prefers-color-scheme: dark) {
  .header {
    background: rgba(26, 23, 38, 0.9);
  }

  .search-box {
    background: rgba(255, 255, 255, 0.05);
    border-color: rgba(255, 255, 255, 0.1);
  }

  .search-shortcut {
    background: rgba(255, 255, 255, 0.1);
    border-color: rgba(255, 255, 255, 0.1);
  }

  .tabs-bar {
    background: var(--cm-bg-secondary);
  }

  .user-dropdown {
    background: var(--cm-bg-secondary);
    border-color: rgba(255, 255, 255, 0.1);
  }

  .dropdown-divider {
    background: rgba(255, 255, 255, 0.1);
  }
}

/* 响应式 */
@media (max-width: 768px) {
  .sidebar {
    transform: translateX(-100%);
  }

  .sidebar.collapsed {
    transform: translateX(-100%);
  }

  .main-area {
    margin-left: 0;
  }

  .search-box {
    display: none;
  }

  .user-name {
    display: none;
  }
}
</style>
