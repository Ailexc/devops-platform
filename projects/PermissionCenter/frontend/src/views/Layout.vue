<template>
  <div class="layout" :class="{ 'demo-fullscreen': isDemoMode }">
    <!-- 侧边栏 -->
    <aside class="sidebar" :class="{ collapsed: sidebarCollapsed, 'demo-hidden': isDemoMode }">
      <div class="brand">
        <div class="brand-logo">PC</div>
        <div v-show="!sidebarCollapsed">
          <div class="brand-name">Permission Center</div>
          <div class="brand-sub">权限中心控制台</div>
        </div>
        <button class="collapse-btn" @click="sidebarCollapsed = !sidebarCollapsed" :title="sidebarCollapsed ? '展开侧栏' : '收起侧栏'">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline :points="sidebarCollapsed ? '9 18 15 12 9 6' : '15 18 9 12 15 6'"/></svg>
        </button>
      </div>

      <nav class="nav">
        <div class="nav-section">总览</div>
        <router-link to="/" class="nav-item" :class="{ active: $route.path === '/' }">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="3" width="7" height="7" rx="1.5"/><rect x="14" y="3" width="7" height="7" rx="1.5"/><rect x="3" y="14" width="7" height="7" rx="1.5"/><rect x="14" y="14" width="7" height="7" rx="1.5"/></svg>
          <span>工作台</span>
        </router-link>

        <div class="nav-section">个人权限</div>
        <router-link to="/me/permissions" class="nav-item" :class="{ active: $route.path === '/me/permissions' }">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/></svg>
          <span>我的权限</span>
        </router-link>
        <router-link to="/me/groups" class="nav-item" :class="{ active: $route.path === '/me/groups' }">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 0 0-3-3.87M16 3.13a4 4 0 0 1 0 7.75"/></svg>
          <span>我的自建组</span>
        </router-link>

        <div class="nav-section">权限市场</div>
        <router-link to="/marketplace" class="nav-item" :class="{ active: $route.path === '/marketplace' }">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M6 2 3 6v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2V6l-3-4z"/><path d="M3 6h18"/><path d="M16 10a4 4 0 0 1-8 0"/></svg>
          <span>能力市场</span>
        </router-link>
        <router-link to="/app-market" class="nav-item" :class="{ active: $route.path === '/app-market' }">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="2" y="3" width="20" height="14" rx="2"/><path d="M8 21h8M12 17v4"/><path d="M7 10l2.5 2.5L17 5"/></svg>
          <span>应用市场</span>
        </router-link>

        <div class="nav-section">审批中心</div>
        <router-link to="/requests" class="nav-item" :class="{ active: $route.path.startsWith('/requests') }">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M9 5H7a2 2 0 0 0-2 2v12a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2V7a2 2 0 0 0-2-2h-2"/><rect x="9" y="3" width="6" height="4" rx="1"/><path d="M9 13h6M9 17h4"/></svg>
          <span>审批中心</span>
          <span v-if="pendingCount" class="nav-badge">{{ pendingCount }}</span>
        </router-link>

        <div class="nav-section">应用与能力</div>
        <router-link to="/apps" class="nav-item" :class="{ active: $route.path === '/apps' || ($route.path.startsWith('/apps/') && !$route.path.includes('/capabilities')) }">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="2" y="3" width="20" height="14" rx="2"/><path d="M8 21h8M12 17v4"/></svg>
          <span>应用管理</span>
        </router-link>
        <router-link to="/capabilities" class="nav-item" :class="{ active: $route.path === '/capabilities' || $route.path.includes('/capabilities/') }">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><path d="M14 2v6h6"/><path d="M12 12v6M9 15h6"/></svg>
          <span>能力管理</span>
        </router-link>

        <div class="nav-section">审计与合规</div>
        <router-link to="/audit" class="nav-item" :class="{ active: $route.path === '/audit' }">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><path d="M14 2v6h6"/><path d="M16 13H8M16 17H8M10 9H8"/></svg>
          <span>审计日志</span>
        </router-link>
        <router-link to="/subjects" class="nav-item" :class="{ active: $route.path === '/subjects' }">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/></svg>
          <span>授权主体</span>
        </router-link>

        <div class="nav-section">系统观测</div>
        <router-link to="/observability/trace" class="nav-item" :class="{ active: $route.path.startsWith('/observability/trace') }">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/></svg>
          <span>鉴权链路追踪</span>
        </router-link>
        <router-link to="/observability/resolver" class="nav-item" :class="{ active: $route.path.startsWith('/observability/resolver') }">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="11" cy="11" r="8"/><path d="m21 21-4.35-4.35"/></svg>
          <span>PEP 解析工作台</span>
        </router-link>
        <router-link to="/observability/pip" class="nav-item" :class="{ active: $route.path.startsWith('/observability/pip') }">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M1 4v6h6"/><path d="M23 20v-6h-6"/><path d="M20.49 9A9 9 0 0 0 5.64 5.64L1 10"/><path d="M3.51 15a9 9 0 0 0 14.85 3.36L23 14"/></svg>
          <span>身份解析（PIP）</span>
        </router-link>
        <router-link to="/observability/cache" class="nav-item" :class="{ active: $route.path.startsWith('/observability/cache') }">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><ellipse cx="12" cy="5" rx="9" ry="3"/><path d="M21 12c0 1.66-4 3-9 3s-9-1.34-9-3"/><path d="M3 5v14c0 1.66 4 3 9 3s9-1.34 9-3V5"/></svg>
          <span>决策缓存工作台</span>
        </router-link>
        <router-link to="/observability/metrics" class="nav-item" :class="{ active: $route.path.startsWith('/observability/metrics') }">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M3 3v18h18"/><path d="M7 14l4-4 3 3 5-6"/></svg>
          <span>鉴权指标面板</span>
        </router-link>
        <router-link to="/observability/owners" class="nav-item" :class="{ active: $route.path.startsWith('/observability/owners') }">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/><path d="M9 12l2 2 4-4"/></svg>
          <span>Owner 巡检视图</span>
        </router-link>
        <router-link to="/observability/agents" class="nav-item" :class="{ active: $route.path.startsWith('/observability/agents') }">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="2" y="3" width="20" height="14" rx="2"/><path d="M8 21h8M12 17v4"/><circle cx="12" cy="10" r="2"/></svg>
          <span>Agent · 分发 · 同步</span>
        </router-link>

        <template v-if="isAdmin">
          <div class="nav-section">管理设置</div>
          <!-- 组织与组：内部概念，不在导航展示 -->
          <router-link to="/policies" class="nav-item" :class="{ active: $route.path === '/policies' }">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/><path d="M12 8v4M12 16h.01"/></svg>
            <span>策略管理</span>
          </router-link>
          <router-link to="/users" class="nav-item" :class="{ active: $route.path === '/users' }">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 0 0-3-3.87M16 3.13a4 4 0 0 1 0 7.75"/></svg>
            <span>用户管理</span>
          </router-link>
        </template>

        <div class="nav-section">系统知识库</div>
        <router-link to="/knowledge/docs" class="nav-item" :class="{ active: $route.path === '/knowledge/docs' }">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><path d="M14 2v6h6"/><path d="M16 13H8M16 17H8M10 9H8"/></svg>
          <span>系统文档</span>
        </router-link>
        <router-link to="/knowledge/interview" class="nav-item" :class="{ active: $route.path === '/knowledge/interview' }">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><path d="M9.09 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3"/><path d="M12 17h.01"/></svg>
          <span>面试题库</span>
        </router-link>

        <div class="nav-section">演示</div>
        <router-link to="/demo" class="nav-item demo-nav" :class="{ active: $route.path === '/demo' }">
          <span style="font-size:16px">🎬</span>
          <span>演示模式</span>
        </router-link>
      </nav>

      <div class="sidebar-foot">
        <div class="user-chip">
          <div class="avatar">{{ (user?.display_name || user?.username || '?')[0] }}</div>
          <div class="user-info">
            <div class="user-name">{{ user?.display_name || user?.username }}</div>
            <div class="user-username mono">{{ user?.username }}</div>
          </div>
        </div>
        <button class="logout-btn" @click="logout">
          <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"/><polyline points="16 17 21 12 16 7"/><line x1="21" y1="12" x2="9" y2="12"/></svg>
          退出
        </button>
      </div>
    </aside>

    <!-- 主区域 -->
    <main class="main">
      <template v-if="!isDemoMode">
      <div class="topbar">
        <div class="crumb">
          <template v-for="(c, i) in crumbs" :key="i">
            <router-link v-if="c.path && i < crumbs.length - 1" :to="c.path" class="crumb-link">{{ c.title }}</router-link>
            <template v-else><b>{{ c.title }}</b></template>
            <span v-if="i < crumbs.length - 1" class="crumb-sep">/</span>
          </template>
        </div>
        <div class="topbar-actions">
          <div class="search-wrap">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="11" cy="11" r="8"/><path d="m21 21-4.35-4.35"/></svg>
            <input v-model="q" class="search-input" placeholder="搜索应用 / 能力 / 权限点…" @focus="searchOpen = true" @input="debouncedSearch" @keydown.esc="searchOpen = false" />
            <div v-if="searchOpen && searchResults" class="search-drop">
              <div v-for="(g, gi) in searchGroups" :key="gi" class="search-group">
                <div class="search-group-title">{{ g.title }}</div>
                <div v-for="r in g.items" :key="g.key + r.id" class="search-item" @mousedown.prevent="go(r)">
                  <span class="mono">{{ r.code || r.id }}</span>
                  <span class="search-name">{{ r.name }}</span>
                </div>
                <div v-if="!g.items.length" class="search-empty">无结果</div>
              </div>
            </div>
          </div>
          <button class="btn btn-ghost theme-btn" @click="theme.toggle()" :title="theme.isDark ? '切换亮色' : '切换暗色'">
            <svg v-if="theme.isDark" width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="5"/><path d="M12 1v2M12 21v2M4.22 4.22l1.42 1.42M18.36 18.36l1.42 1.42M1 12h2M21 12h2M4.22 19.78l1.42-1.42M18.36 5.64l1.42-1.42"/></svg>
            <svg v-else width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/></svg>
          </button>
          <router-link to="/marketplace" class="btn btn-primary">＋ 申请权限</router-link>
        </div>
      </div>
      </template>
      <div class="content">
        <router-view />
      </div>
    </main>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useThemeStore } from '../stores/theme'
import { api } from '../api/client'

const route = useRoute()
const router = useRouter()
const theme = useThemeStore()
const user = ref<any>(null)
const isAdmin = computed(() => user.value?.username === 'admin')
const isDemoMode = computed(() => route.path.startsWith('/demo'))

const q = ref('')
const searchOpen = ref(false)
const searchResults = ref<any>(null)
const pendingCount = ref(0)
const sidebarCollapsed = ref(false)

const crumbs = computed(() => {
  const meta = (route.meta as any).crumb as Array<{ title: string; path?: string }> | undefined
  if (meta?.length) return meta
  return [{ title: (route.meta as any).title || '工作台' }]
})

const searchGroups = computed(() => {
  const r = searchResults.value
  if (!r) return []
  return [
    { title: '应用', key: 'app', items: r.apps.slice(0, 6) },
    { title: '能力', key: 'cap', items: r.caps.slice(0, 6) },
    { title: '组织 / 组', key: 'group', items: r.groups.slice(0, 6) },
  ]
})

let timer: any = null
function debouncedSearch() {
  clearTimeout(timer)
  timer = setTimeout(doSearch, 250)
}
async function doSearch() {
  const kw = q.value.trim()
  if (!kw) { searchResults.value = null; return }
  try {
    const [apps, caps, groups] = await Promise.all([api.marketplaceApps(), api.marketplaceCapabilities(), api.groups()])
    const k = kw.toLowerCase()
    searchResults.value = {
      apps: ((apps as any).items || []).filter((a: any) => (a.name + a.code + (a.openapi_url || '')).toLowerCase().includes(k)).map((a: any) => ({ id: a.id, code: a.code, name: a.name, to: `/apps/${a.id}` })),
      caps: ((caps as any).items || []).filter((c: any) => (c.name + c.description + (c.app_name || '')).toLowerCase().includes(k)).map((c: any) => ({ id: c.id, code: c.app_code, name: c.name, to: `/capabilities` })),
      groups: ((groups as any).items || []).filter((g: any) => g.name.toLowerCase().includes(k)).map((g: any) => ({ id: g.id, code: 'grp', name: g.name, to: g.type === 2 ? `/groups/${g.id}` : `/groups/${g.id}` })),
    }
  } catch { searchResults.value = null }
}
function go(r: any) {
  searchOpen.value = false
  q.value = ''
  searchResults.value = null
  router.push(r.to)
}

async function loadPending() {
  try {
    const r: any = await api.requestsByRole('approver')
    pendingCount.value = (r.items || []).filter((x: any) => x.status === 1).length
  } catch { /* ignore */ }
}

function onPendingChanged() { loadPending() }

function logout() {
  localStorage.removeItem('iam_token')
  localStorage.removeItem('iam_user')
  router.push('/login')
}

onMounted(() => {
  try {
    user.value = JSON.parse(localStorage.getItem('iam_user') || 'null')
  } catch { /* ignore */ }
  loadPending()
  // 审批动作（通过/驳回/切换视角）后即时刷新侧栏待审批红点
  window.addEventListener('iam:pending-changed', onPendingChanged)
})
</script>

<style scoped>
.layout { display: flex; min-height: 100vh; }
.layout.demo-fullscreen { flex-direction: column; }
.layout.demo-fullscreen .main { width: 100%; }

/* ---- 侧边栏 ---- */
.sidebar { width: 232px; flex-shrink: 0; background: var(--bg-card); border-right: 1px solid var(--border); display: flex; flex-direction: column; position: sticky; top: 0; height: 100vh; }
.brand { display: flex; align-items: center; gap: 10px; padding: 18px 20px; border-bottom: 1px solid var(--border); }
.sidebar.collapsed .brand { padding: 18px 10px; justify-content: center; gap: 0; }
.brand-logo { width: 32px; height: 32px; border-radius: 8px; background: linear-gradient(135deg, var(--brand), var(--brand-strong)); color: #fff; display: flex; align-items: center; justify-content: center; font-weight: 700; font-size: 13px; flex-shrink: 0; }
.brand-name { font-size: 14px; font-weight: 700; color: var(--text); }
.brand-sub { font-size: 11px; color: var(--text-tertiary); letter-spacing: .02em; }
.collapse-btn { margin-left: auto; background: none; border: none; cursor: pointer; color: var(--text-tertiary); padding: 4px; border-radius: 4px; display: flex; align-items: center; transition: color .15s; }
.collapse-btn:hover { color: var(--text); background: var(--bg-hover); }
.sidebar.collapsed .collapse-btn { margin-left: 0; }

/* 收起状态 */
.sidebar.collapsed { width: 60px; transition: width 0.2s ease; }
.sidebar.collapsed .nav-section { display: none; }
.sidebar.collapsed .nav-item { justify-content: center; padding: 10px; gap: 0; font-size: 0; }
.sidebar.collapsed .nav-item span { display: none; }
.sidebar.collapsed .nav-item svg { margin: 0; }
.sidebar.collapsed .nav-badge { position: absolute; top: 2px; right: 2px; min-width: 14px; height: 14px; font-size: 8px; padding: 0 3px; }
.sidebar.collapsed .sidebar-foot { padding: 10px 6px; justify-content: center; }
.sidebar.collapsed .user-info { display: none; }
.sidebar.collapsed .user-chip { justify-content: center; padding: 6px; }
.sidebar.collapsed .logout-btn { font-size: 0; padding: 6px; }
.sidebar.collapsed .logout-btn svg { margin: 0; }
.sidebar.collapsed .demo-nav { font-size: 0; justify-content: center; padding: 10px; }
.sidebar.collapsed .demo-nav span { display: none; }

.nav { flex: 1; padding: 12px 10px; overflow-y: auto; }
.nav-section { font-size: 11px; font-weight: 600; color: var(--text-tertiary); text-transform: uppercase; letter-spacing: .06em; padding: 16px 12px 6px; }
.nav-item { display: flex; align-items: center; gap: 10px; padding: 8px 12px; margin: 1px 0; border-radius: 8px; font-size: 13px; font-weight: 500; color: var(--text-secondary); cursor: pointer; transition: background .15s, color .15s; position: relative; }
.nav-item svg { flex-shrink: 0; opacity: .85; }
.nav-item:hover { background: var(--bg-hover); color: var(--text); }
.nav-item.active { background: var(--brand-soft); color: var(--brand-strong); font-weight: 600; }
.nav-item.active svg { stroke: var(--brand-strong); opacity: 1; }
.nav-badge { margin-left: auto; min-width: 18px; height: 18px; border-radius: 999px; background: var(--danger); color: #fff; font-size: 10px; display: inline-flex; align-items: center; justify-content: center; padding: 0 5px; }
.demo-nav { background: linear-gradient(135deg, var(--brand-soft), var(--purple-bg)) !important; border: 1px solid var(--brand) !important; margin-top: 8px; }
.demo-nav.active { background: linear-gradient(135deg, var(--brand), var(--purple)) !important; color: #fff !important; }

.sidebar-foot { padding: 12px; border-top: 1px solid var(--border); display: flex; align-items: center; gap: 8px; }
.user-chip { display: flex; align-items: center; gap: 10px; padding: 6px 8px; border-radius: 8px; flex: 1; }
.avatar { width: 30px; height: 30px; border-radius: 50%; background: linear-gradient(135deg, #60a5fa, var(--brand)); color: #fff; display: flex; align-items: center; justify-content: center; font-size: 13px; font-weight: 600; flex-shrink: 0; }
.user-info { min-width: 0; }
.user-name { font-size: 13px; font-weight: 600; }
.user-username { font-size: 11px; color: var(--text-tertiary); }
.logout-btn { display: inline-flex; align-items: center; gap: 4px; background: none; border: none; color: var(--text-tertiary); font-size: 11px; cursor: pointer; padding: 6px; border-radius: 6px; }
.logout-btn:hover { background: var(--bg-hover); color: var(--danger); }

/* ---- 主区域 ---- */
.main { flex: 1; min-width: 0; display: flex; flex-direction: column; }
.topbar { height: 56px; background: var(--bg-card); border-bottom: 1px solid var(--border); display: flex; align-items: center; justify-content: space-between; padding: 0 24px; position: sticky; top: 0; z-index: 50; gap: 16px; }
.crumb { font-size: 13px; color: var(--text-tertiary); display: flex; align-items: center; gap: 6px; min-width: 0; }
.crumb b { color: var(--text); font-weight: 600; }
.crumb-link { color: var(--text-tertiary); }
.crumb-link:hover { color: var(--brand); }
.crumb-sep { color: var(--border-strong); }
.topbar-actions { display: flex; align-items: center; gap: 10px; }

.search-wrap { position: relative; width: 260px; }
.search-wrap > svg { position: absolute; left: 10px; top: 50%; transform: translateY(-50%); color: var(--text-tertiary); }
.search-input { width: 100%; height: 34px; padding: 0 12px 0 32px; background: var(--bg-inset); border: 1px solid var(--border); border-radius: 8px; color: var(--text); font-size: 13px; outline: none; transition: border-color .15s, box-shadow .15s; }
.search-input:focus { border-color: var(--brand); box-shadow: 0 0 0 3px rgba(47,111,237,.12); }
.search-drop { position: absolute; top: 40px; left: 0; right: 0; background: var(--bg-card); border: 1px solid var(--border); border-radius: 10px; box-shadow: var(--shadow-lg); padding: 8px; max-height: 360px; overflow-y: auto; }
.search-group-title { font-size: 10px; font-weight: 600; color: var(--text-tertiary); text-transform: uppercase; letter-spacing: .05em; padding: 6px 8px 2px; }
.search-item { display: flex; gap: 8px; padding: 7px 8px; border-radius: 6px; cursor: pointer; font-size: 13px; }
.search-item:hover { background: var(--bg-hover); }
.search-item .mono { color: var(--text-tertiary); }
.search-empty { padding: 4px 8px; font-size: 12px; color: var(--text-tertiary); }

.btn { display: inline-flex; align-items: center; gap: 6px; height: 34px; padding: 0 14px; border-radius: 8px; font-size: 13px; font-weight: 600; cursor: pointer; border: 1px solid transparent; transition: all .15s; text-decoration: none; }
.btn-primary { background: var(--brand); color: #fff; }
.btn-primary:hover { background: var(--brand-strong); }
.btn-ghost { background: transparent; color: var(--text-secondary); border-color: var(--border); }
.btn-ghost:hover { background: var(--bg-hover); color: var(--text); border-color: var(--border-strong); }
.theme-btn { width: 34px; padding: 0; justify-content: center; }

.content { padding: 24px; max-width: 1200px; width: 100%; margin: 0 auto; flex: 1; }
.layout.demo-fullscreen .content { max-width: none; padding: 0; }

/* 侧栏过渡动画 */
.sidebar.demo-hidden {
  display: none;
}

@media (max-width: 900px) {
  .sidebar { display: none; }
  .search-wrap { width: 160px; }
}
</style>
