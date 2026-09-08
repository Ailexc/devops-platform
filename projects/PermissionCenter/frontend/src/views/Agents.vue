<template>
  <div class="agents-page">
    <header class="page-header">
      <h1>Agent / 分发 / 同步</h1>
      <span class="page-desc">策略下发到 agent 的工作记录：在线状态 · 版本一致性 · 分发历史 · 同步任务</span>
    </header>

    <div class="tabs">
      <button class="tab" :class="{ active: tab === 'agents' }" @click="switchTab('agents')">Agent 状态</button>
      <button class="tab" :class="{ active: tab === 'bundles' }" @click="switchTab('bundles')">策略分发记录</button>
      <button class="tab" :class="{ active: tab === 'sync' }" @click="switchTab('sync')">同步任务</button>
    </div>

    <!-- Agent 状态 -->
    <div v-if="tab === 'agents'" class="panel">
      <div v-if="agents.length === 0" class="empty-state">暂无 agent 上报（iam-agent 启动后会定期上报状态）</div>
      <div v-for="a in agents" :key="a.agent_id" class="agent-card">
        <div class="agent-head">
          <div>
            <span class="mono agent-id">{{ a.agent_id }}</span>
            <span class="tag" :class="a.online ? 'tag-success' : 'tag-danger'">{{ a.online ? '在线' : '离线' }}</span>
            <span class="text-secondary" style="font-size: 12px; margin-left: 8px;">{{ a.app_name || ('app#' + a.app_id) }}</span>
          </div>
          <div class="rev-box">
            <span class="mono rev">{{ a.current_rev }}</span>
            <span class="rev-sep">/</span>
            <span class="mono rev" :class="a.latest_rev !== null && a.behind ? 'rev-behind' : ''">{{ a.latest_rev ?? '—' }}</span>
            <span v-if="a.behind" class="tag tag-warn">版本落后</span>
            <span v-else-if="a.latest_rev !== null" class="tag tag-success">已同步</span>
          </div>
        </div>
        <div class="agent-body">
          <div class="metric"><span class="m-label">心跳</span><span class="mono">{{ fmtTime(a.last_seen_at) }}</span></div>
          <div class="metric"><span class="m-label">决策量</span><span class="mono">{{ a.decision_count }}</span></div>
          <div class="metric"><span class="m-label">本地命中率</span><span class="mono">{{ (a.hit_rate * 100).toFixed(1) }}%</span></div>
        </div>
      </div>
    </div>

    <!-- Bundle 分发记录 -->
    <div v-if="tab === 'bundles'" class="panel">
      <div class="panel-toolbar">
        <select v-model="bundleApp" class="select">
          <option v-for="a in apps" :key="a.id" :value="a.id">{{ a.code }} ({{ a.name }})</option>
        </select>
      </div>
      <table class="data-table">
        <thead><tr><th>版本</th><th>校验和</th><th>策略数</th><th>组规则数</th><th>发布人</th><th>时间</th><th></th></tr></thead>
        <tbody>
          <template v-for="b in bundles" :key="b.id">
            <tr>
              <td class="mono">v{{ b.revision }}</td>
              <td class="mono">{{ b.checksum }}</td>
              <td class="mono">{{ b.policy_count }}</td>
              <td class="mono">{{ b.grouping_count }}</td>
              <td class="mono">{{ b.published_by || '—' }}</td>
              <td class="mono text-secondary" style="white-space: nowrap;">{{ fmtTime(b.created_at) }}</td>
              <td>
                <button class="btn btn-sm" @click="openBundle = openBundle === b.id ? 0 : b.id">
                  📦 内容 {{ openBundle === b.id ? '▾' : '▸' }}
                </button>
              </td>
            </tr>
            <tr v-if="openBundle === b.id" class="bundle-ep-row">
              <td colspan="7">
                <div v-if="b.policy_preview?.length" class="ep-list">
                  <div class="ep-item" v-for="(p, i) in b.policy_preview" :key="i">
                    <span class="mono ep-subject">{{ p.subject_key }}</span>
                    <span class="mono ep-app">{{ p.app_code }}</span>
                    <span class="mono ep-actions">{{ (p.actions || []).join(', ') }}</span>
                    <span class="tag" :class="p.effect === 'allow' ? 'tag-success' : 'tag-danger'">{{ p.effect }}</span>
                  </div>
                  <div v-if="b.policy_count > b.policy_preview.length" class="text-secondary" style="font-size:12px;">… 共 {{ b.policy_count }} 条策略（预览前 {{ b.policy_preview.length }} 条）</div>
                </div>
                <div v-else class="empty-state">该版本无策略内容</div>
                <div v-if="b.force_remote?.length" class="force-remote">🔒 强制回源动作：<span v-for="f in b.force_remote" :key="f" class="mono fr-chip">{{ f }}</span></div>
              </td>
            </tr>
          </template>
        </tbody>
      </table>
      <div v-if="bundles.length === 0" class="empty-state">暂无分发记录</div>
    </div>

    <!-- 同步任务 -->
    <div v-if="tab === 'sync'" class="panel">
      <table class="data-table">
        <thead><tr><th>ID</th><th>类型</th><th>状态</th><th>开始</th><th>结束</th><th>耗时</th><th>结果</th></tr></thead>
        <tbody>
          <tr v-for="j in jobs" :key="j.id">
            <td class="mono">{{ j.id }}</td>
            <td>{{ j.type_name }}</td>
            <td><span class="tag" :class="jobClass(j.status)">{{ j.status_name }}</span></td>
            <td class="mono text-secondary">{{ fmtTime(j.started_at) }}</td>
            <td class="mono text-secondary">{{ fmtTime(j.finished_at) }}</td>
            <td class="mono">{{ j.duration || '—' }}</td>
            <td class="mono text-secondary" style="max-width: 240px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">
              {{ j.result ? JSON.stringify(j.result) : '—' }}
            </td>
          </tr>
        </tbody>
      </table>
      <div v-if="jobs.length === 0" class="empty-state">暂无同步任务</div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { api } from '../api/client'

const tab = ref<'agents' | 'bundles' | 'sync'>('agents')
const agents = ref<any[]>([])
const apps = ref<any[]>([])
const bundles = ref<any[]>([])
const jobs = ref<any[]>([])
const bundleApp = ref<number>(1)
const openBundle = ref(0)

async function load() {
  if (tab.value === 'agents') {
    const d = await api.agents()
    agents.value = (d as any).items || []
  } else if (tab.value === 'bundles') {
    if (apps.value.length === 0) {
      const a = await api.apps()
      apps.value = (a as any).items || []
    }
    const d = await api.bundles(bundleApp.value)
    bundles.value = (d as any).items || []
  } else {
    const d = await api.syncJobs()
    jobs.value = (d as any).items || []
  }
}

function switchTab(t: 'agents' | 'bundles' | 'sync') {
  tab.value = t
  load()
}

function jobClass(s: number): string {
  return { 0: 'tag-danger', 1: 'tag-warn', 2: 'tag-success' }[s] || ''
}
function fmtTime(t: string): string {
  if (!t) return '—'
  try { return new Date(t).toLocaleString('zh-CN') } catch { return t }
}

onMounted(load)
</script>

<style scoped>
.agents-page { max-width: 1400px; }
.page-header { margin-bottom: 20px; }
.page-header h1 { font-size: 24px; font-weight: 700; letter-spacing: -0.5px; margin-bottom: 4px; }
.page-desc { font-size: 13px; color: var(--text-secondary); }

.tabs { display: flex; gap: 0; border: 1px solid var(--border); width: fit-content; }
.tab { padding: 8px 20px; font-size: 13px; font-weight: 500; background: var(--bg); border: none; border-right: 1px solid var(--border); color: var(--text-secondary); cursor: pointer; font-family: var(--font-mono); }
.tab:last-child { border-right: none; }
.tab:hover { background: var(--bg-hover); color: var(--text); }
.tab.active { background: var(--accent); color: var(--accent-text); font-weight: 600; }

.panel { border: 1px solid var(--border); border-top: none; background: var(--bg); }
.panel-toolbar { display: flex; justify-content: flex-start; padding: 12px 16px; border-bottom: 1px solid var(--border); }
.select { padding: 6px 10px; font-size: 12px; font-family: var(--font-mono); border: 1px solid var(--border); background: var(--bg); color: var(--text); }

.agent-card { border-bottom: 1px solid var(--border); }
.agent-card:last-child { border-bottom: none; }
.agent-head { display: flex; justify-content: space-between; align-items: center; padding: 14px 16px; background: var(--bg-secondary); }
.agent-id { font-size: 13px; font-weight: 600; margin-right: 10px; }
.rev-box { display: flex; align-items: center; gap: 6px; }
.rev { font-size: 14px; font-weight: 700; }
.rev-behind { color: #ef4444; }
.rev-sep { color: var(--text-tertiary); }
.agent-body { display: flex; gap: 32px; padding: 12px 16px; }
.metric { display: flex; flex-direction: column; gap: 2px; }
.m-label { font-size: 10px; text-transform: uppercase; letter-spacing: 1px; color: var(--text-secondary); font-family: var(--font-mono); }

.data-table { width: 100%; border-collapse: collapse; font-size: 13px; }
.data-table th { text-align: left; padding: 10px 14px; font-family: var(--font-mono); font-size: 10px; font-weight: 600; text-transform: uppercase; letter-spacing: 1px; color: var(--text-secondary); background: var(--bg-secondary); border-bottom: 1px solid var(--border); }
.data-table td { padding: 9px 14px; border-bottom: 1px solid var(--border); }

.tag { font-family: var(--font-mono); font-size: 10px; font-weight: 600; padding: 2px 8px; background: var(--bg-tertiary); text-transform: uppercase; letter-spacing: 0.5px; }
.tag-success { background: rgba(34, 197, 94, 0.15); color: #22c55e; }
.tag-danger { background: rgba(239, 68, 68, 0.15); color: #ef4444; }
.tag-warn { background: rgba(245, 158, 11, 0.15); color: #f59e0b; }
.mono { font-family: var(--font-mono); font-size: 12px; }
.text-secondary { color: var(--text-secondary); }
.empty-state { padding: 32px; text-align: center; color: var(--text-tertiary); font-size: 13px; }

/* bundle 内容展开（G4） */
.bundle-ep-row td { background: var(--bg-secondary); }
.ep-list { display: flex; flex-direction: column; gap: 6px; }
.ep-item { display: flex; align-items: center; gap: 10px; flex-wrap: wrap; padding: 7px 10px; border: 1px solid var(--border); border-radius: 6px; background: var(--bg-card); font-size: 12px; }
.ep-subject { font-weight: 700; color: var(--brand); }
.ep-app { color: var(--text-secondary); }
.ep-actions { color: var(--text); }
.force-remote { margin-top: 8px; font-size: 12px; color: var(--text-secondary); }
.fr-chip { display: inline-block; padding: 1px 6px; margin-right: 4px; background: rgba(245,158,11,.12); color: #d97706; border-radius: 4px; }
.btn { padding: 6px 14px; font-size: 12px; font-weight: 600; border: 1px solid var(--border); border-radius: 8px; background: var(--bg-card); color: var(--text); cursor: pointer; }
.btn-sm { padding: 3px 10px; font-size: 11px; }
</style>
