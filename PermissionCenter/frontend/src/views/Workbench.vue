<template>
  <div class="workbench">
    <PageHeader title="工作台" desc="以「我」为中心 —— 权限、待办、应用与快捷入口">
      <template #actions>
        <router-link to="/marketplace" class="btn btn-primary">＋ 申请权限</router-link>
      </template>
    </PageHeader>

    <div v-if="overview" class="identity-card" @click="$router.push('/me/groups')">
      <div class="identity-main">
        <span class="avatar">{{ (overview.user?.display_name || overview.user?.username || '?').slice(0, 1) }}</span>
        <div>
          <div class="identity-name">{{ overview.user?.display_name || overview.user?.username }}</div>
          <div class="identity-sub">{{ identitySummary }}</div>
        </div>
      </div>
      <span class="identity-arrow">→ 我的身份</span>
    </div>

    <div class="stats">
      <StatCard icon="🏢" :value="stats[0].value" label="组织权限" tone="blue" @click="$router.push('/me/permissions')" />
      <StatCard icon="👤" :value="stats[1].value" label="个人权限" tone="green" @click="$router.push('/me/permissions')" />
      <StatCard icon="👥" :value="stats[2].value" label="自建组权限" tone="amber" @click="$router.push('/me/groups')" />
      <StatCard icon="📦" :value="stats[3].value" label="负责应用" tone="violet" @click="$router.push('/apps')" />
    </div>

    <div class="grid-2">
      <PanelCard title="待办事项" sub="全部 → 审批中心">
        <template #actions><router-link to="/requests" class="panel-link">全部</router-link></template>
        <div class="todo-row" @click="$router.push('/requests?role=approver')">
          <span>待我审批</span><span class="todo-badge" :class="{ has: todos.pending_approvals > 0 }">{{ todos.pending_approvals }}</span>
        </div>
        <div class="todo-row" @click="$router.push('/requests')">
          <span>进行中的申请</span><span class="todo-badge" :class="{ has: todos.in_progress_requests > 0 }">{{ todos.in_progress_requests }}</span>
        </div>
      </PanelCard>

      <PanelCard title="我的应用" sub="管理">
        <template #actions><router-link to="/apps" class="panel-link">管理</router-link></template>
        <div v-if="!(overview?.identity?.owned_apps || []).length" class="empty-state">暂无拥有的应用</div>
        <div v-for="a in overview?.identity?.owned_apps || []" :key="a.id" class="row" @click="$router.push(`/apps/${a.id}`)">
          <span class="mono">{{ a.code }}</span><span style="flex:1;">{{ a.name }}</span>
          <span class="tag" :class="a.status === 1 ? 'tag-ok' : 'tag-red'">{{ a.status === 1 ? 'active' : 'disabled' }}</span>
        </div>
      </PanelCard>

      <PanelCard title="我的自建组">
        <template #actions><router-link to="/me/groups" class="panel-link">管理</router-link></template>
        <div v-if="!(overview?.identity?.custom_groups || []).length" class="empty-state">暂无自建组</div>
        <div v-for="g in overview?.identity?.custom_groups || []" :key="g.id" class="row" @click="$router.push(`/groups/${g.id}`)">
          <span class="mono">{{ g.id }}</span><span style="flex:1;">{{ g.name }}</span>
          <span class="tag tag-gray">{{ g.status === 1 ? 'active' : 'expired' }}</span>
        </div>
      </PanelCard>

      <PanelCard title="快捷入口">
        <div class="quick-grid">
          <div class="quick-entry" @click="$router.push('/marketplace')">🔖 能力市场</div>
          <div class="quick-entry" @click="$router.push('/app-market')">🔑 应用市场</div>
          <div class="quick-entry" @click="$router.push('/capabilities')">📦 能力管理</div>
          <div class="quick-entry" @click="$router.push('/me/permissions')">👤 我的权限</div>
        </div>
      </PanelCard>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { api } from '../api/client'
import PageHeader from '../components/PageHeader.vue'
import StatCard from '../components/StatCard.vue'
import PanelCard from '../components/PanelCard.vue'

const overview = ref<any>(null)

const stats = computed(() => {
  const pc = overview.value?.permission_counts || {}
  return [
    { value: pc.organization ?? 0 },
    { value: pc.personal ?? 0 },
    { value: pc.custom_group ?? 0 },
    { value: (overview.value?.identity?.owned_apps || []).length },
  ]
})
const todos = computed(() => {
  const t = overview.value?.todos || {}
  return { pending_approvals: t.pending_approvals ?? 0, in_progress_requests: t.in_progress_requests ?? 0 }
})
const identitySummary = computed(() => {
  const id = overview.value?.identity || {}
  const parts: string[] = []
  const orgs = id.orgs || []
  if (orgs.length) parts.push(`组织：${orgs.map((g: any) => (g.path_names || [g.name]).join('→')).join('、')}`)
  const apps = id.owned_apps || []
  if (apps.length) parts.push(`应用 owner：${apps.length} 个`)
  if (id.approver) parts.push('审批人')
  return parts.join(' · ') || '暂无身份信息'
})

onMounted(async () => {
  try { overview.value = await api.meOverview() } catch { /* partial load ok */ }
})
</script>

<style scoped>
.identity-card { display: flex; justify-content: space-between; align-items: center; padding: 16px 20px; background: var(--bg-card); border: 1px solid var(--border); border-radius: var(--radius); box-shadow: var(--shadow-sm); margin-bottom: 20px; cursor: pointer; }
.identity-card:hover { border-color: var(--border-strong); }
.identity-main { display: flex; align-items: center; gap: 14px; }
.avatar { display: flex; align-items: center; justify-content: center; width: 40px; height: 40px; border-radius: 50%; background: linear-gradient(135deg, #60a5fa, var(--brand)); color: #fff; font-weight: 700; font-size: 16px; }
.identity-name { font-size: 16px; font-weight: 700; }
.identity-sub { font-size: 12px; color: var(--text-secondary); }
.identity-arrow { font-size: 13px; color: var(--brand); font-weight: 500; }
.stats { display: grid; grid-template-columns: repeat(4, 1fr); gap: 16px; margin-bottom: 20px; }
.grid-2 { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; }
.todo-row { display: flex; align-items: center; justify-content: space-between; padding: 10px; border-radius: 8px; cursor: pointer; font-size: 13px; }
.todo-row:hover { background: var(--bg-hover); }
.todo-badge { min-width: 22px; height: 22px; border-radius: 999px; display: inline-flex; align-items: center; justify-content: center; background: var(--bg-inset); color: var(--text-tertiary); font-size: 12px; font-weight: 600; }
.todo-badge.has { background: var(--danger); color: #fff; }
.row { display: flex; align-items: center; gap: 10px; padding: 9px 10px; border-radius: 8px; cursor: pointer; font-size: 13px; }
.row:hover { background: var(--bg-hover); }
.quick-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; }
.quick-entry { padding: 14px; border: 1px solid var(--border); border-radius: 8px; cursor: pointer; font-size: 13px; font-weight: 600; text-align: center; }
.quick-entry:hover { border-color: var(--brand); background: var(--brand-softer); color: var(--brand-strong); }
.panel-link { font-size: 12px; color: var(--brand); font-weight: 500; text-decoration: none; }
.panel-link:hover { text-decoration: underline; }
.empty-state { padding: 20px; text-align: center; color: var(--text-tertiary); font-size: 12px; }
.tag { font-family: var(--font-mono); font-size: 10px; font-weight: 600; padding: 2px 8px; border-radius: 999px; }
.tag-ok { background: var(--success-bg); color: var(--success); }
.tag-red { background: var(--danger-bg); color: var(--danger); }
.tag-gray { background: var(--bg-inset); color: var(--text-tertiary); border: 1px solid var(--border); }
.btn { display: inline-flex; align-items: center; gap: 6px; height: 34px; padding: 0 14px; border-radius: 8px; font-size: 13px; font-weight: 600; border: 1px solid var(--border); background: var(--bg-card); color: var(--text); cursor: pointer; text-decoration: none; }
.btn-primary { background: var(--brand); color: #fff; border-color: var(--brand); }
.mono { font-family: var(--font-mono); font-size: 12px; }
@media (max-width: 900px) { .stats { grid-template-columns: repeat(2, 1fr); } .grid-2 { grid-template-columns: 1fr; } }
</style>
