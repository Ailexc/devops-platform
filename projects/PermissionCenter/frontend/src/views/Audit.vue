<template>
  <div class="audit-page">
    <header class="page-header">
      <h1>审计中心</h1>
      <span class="page-desc">我的申请 · 我的审批 · 我的发布 + 全局日志</span>
    </header>

    <div class="tabs">
      <button class="tab" :class="{ active: tab === 'requests' }" @click="setTab('requests')">我的申请</button>
      <button class="tab" :class="{ active: tab === 'approvals' }" @click="setTab('approvals')">我的审批</button>
      <button class="tab" :class="{ active: tab === 'publishes' }" @click="setTab('publishes')">我的发布</button>
      <button class="tab" :class="{ active: tab === 'audit' }" @click="setTab('audit')">全局审计</button>
      <button class="tab" :class="{ active: tab === 'decision' }" @click="setTab('decision')">决策日志</button>
    </div>

    <!-- 我的申请（FR-8） -->
    <div v-if="tab === 'requests'" class="panel">
      <table class="data-table">
        <thead><tr><th>#</th><th>目标应用</th><th>风险</th><th>状态</th><th>审批链</th><th>提交时间</th></tr></thead>
        <tbody>
          <tr v-for="r in myRequests" :key="r.id">
            <td class="mono">{{ r.id }}</td>
            <td><span class="mono">{{ r.app_code }}</span> {{ r.app_name }}</td>
            <td><span class="tag">{{ ['低', '中', '高'][r.risk_level - 1] }}</span></td>
            <td><span class="tag" :class="reqStatusClass(r.status)">{{ reqStatus(r.status) }}</span></td>
            <td class="mono">{{ (r.approval_chain || []).map((a: any) => a.name).join(' → ') || '自动' }}</td>
            <td class="mono text-secondary" style="white-space: nowrap;">{{ formatTime(r.created_at) }}</td>
          </tr>
        </tbody>
      </table>
      <div v-if="myRequests.length === 0" class="empty-state">暂无我发起的申请</div>
    </div>

    <!-- 我的审批（FR-8）：区分"待我确认的授权"（grant）与"待我审批的申请"（apply） -->
    <div v-if="tab === 'approvals'" class="panel">
      <div class="sub-title">待我审批 / 待我确认的授权</div>
      <table class="data-table">
        <thead><tr><th>#</th><th>方向</th><th>申请人</th><th>被授权主体</th><th>目标应用</th><th>风险</th><th>理由</th><th>操作</th></tr></thead>
        <tbody>
          <tr v-for="r in pendingApprovals" :key="r.id">
            <td class="mono">{{ r.id }}</td>
            <td><span class="tag" :class="r.request_type === 2 ? 'tag-warning' : 'tag'">{{ r.request_type === 2 ? '授权确认' : '申请' }}</span></td>
            <td>{{ r.applicant_name }}</td>
            <td class="mono">{{ subjectText(r) }}</td>
            <td><span class="mono">{{ r.app_code }}</span> {{ r.app_name }}</td>
            <td><span class="tag">{{ ['低', '中', '高'][r.risk_level - 1] }}</span></td>
            <td class="text-secondary" style="max-width: 200px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">{{ r.reason || '—' }}</td>
            <td>
              <button class="btn btn-sm btn-primary" @click="approve(r.id, 1)">通过</button>
              <button class="btn btn-sm" @click="approve(r.id, 2)" style="margin-left: 6px;">驳回</button>
            </td>
          </tr>
        </tbody>
      </table>
      <div v-if="pendingApprovals.length === 0" class="empty-state">暂无待我审批 / 待确认</div>
      <div class="sub-title" style="margin-top: 16px;">我审批过的</div>
      <table class="data-table">
        <thead><tr><th>#</th><th>申请人</th><th>目标应用</th><th>结果</th></tr></thead>
        <tbody>
          <tr v-for="r in doneApprovals" :key="r.id">
            <td class="mono">{{ r.id }}</td>
            <td>{{ r.applicant_name }}</td>
            <td><span class="mono">{{ r.app_code }}</span> {{ r.app_name }}</td>
            <td><span class="tag">{{ reqStatus(r.status) }}</span></td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- 我的发布（FR-8） -->
    <div v-if="tab === 'publishes'" class="panel">
      <div class="sub-title">策略 / 授权</div>
      <table class="data-table">
        <thead><tr><th>类型</th><th>名称</th><th>应用</th><th>状态</th><th>时间</th></tr></thead>
        <tbody>
          <tr v-for="(p, i) in publishes.policies || []" :key="'p' + i">
            <td><span class="tag">策略</span></td>
            <td>{{ p.name }}</td>
            <td class="mono">{{ p.app_id }}</td>
            <td>{{ p.status === 1 ? 'active' : 'disabled' }}</td>
            <td class="mono text-secondary" style="white-space: nowrap;">{{ formatTime(p.created_at) }}</td>
          </tr>
          <tr v-for="(t, i) in publishes.templates || []" :key="'t' + i">
            <td><span class="tag">模板</span></td>
            <td>{{ t.name }} <span class="mono text-secondary">（被申请 {{ t.apply_count }}）</span></td>
            <td class="mono">{{ t.app_id }}</td>
            <td>{{ t.status }}</td>
            <td class="mono text-secondary" style="white-space: nowrap;">{{ formatTime(t.created_at) }}</td>
          </tr>
          <tr v-for="(m, i) in publishes.capabilities || []" :key="'c' + i">
            <td><span class="tag">能力</span></td>
            <td>{{ m.name }} <span class="mono text-secondary">v{{ m.version }}</span></td>
            <td class="mono">{{ m.app_id }}</td>
            <td>{{ m.status }}</td>
            <td class="mono text-secondary" style="white-space: nowrap;">{{ formatTime(m.created_at) }}</td>
          </tr>
        </tbody>
      </table>
      <div v-if="!publishes.policies?.length && !publishes.templates?.length && !publishes.capabilities?.length" class="empty-state">暂无发布记录</div>
    </div>

    <!-- 全局审计 -->
    <div v-if="tab === 'audit'" class="panel">
      <table class="data-table">
        <thead>
          <tr><th>ID</th><th>操作人</th><th>动作</th><th>资源</th><th>资源ID</th><th>IP</th><th>时间</th><th>详情</th></tr>
        </thead>
        <tbody>
          <tr v-for="a in audit" :key="a.id">
            <td class="mono">{{ a.id }}</td>
            <td class="mono">{{ a.actor_id }}</td>
            <td>{{ a.action }}</td>
            <td>{{ a.resource_type }}</td>
            <td class="mono">{{ a.resource_id }}</td>
            <td class="mono text-secondary">{{ a.ip }}</td>
            <td class="mono text-secondary" style="white-space: nowrap;">{{ formatTime(a.created_at) }}</td>
            <td class="mono text-secondary" style="max-width: 180px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">
              {{ a.detail ? JSON.stringify(a.detail) : '—' }}
            </td>
          </tr>
        </tbody>
      </table>
      <div v-if="audit.length === 0" class="empty-state">暂无审计记录</div>
    </div>

    <!-- 决策日志 -->
    <div v-if="tab === 'decision'" class="panel">
      <table class="data-table">
        <thead>
          <tr><th>ID</th><th>用户</th><th>应用</th><th>动作</th><th>决策</th><th>渠道</th><th>耗时</th><th>时间</th></tr>
        </thead>
        <tbody>
          <tr v-for="d in decisions" :key="d.id">
            <td class="mono">{{ d.id }}</td>
            <td class="mono">{{ d.user_id }}</td>
            <td class="mono">{{ d.app_id }}</td>
            <td>{{ d.action }}</td>
            <td><span class="tag" :class="d.decision === 1 ? 'tag-success' : 'tag-danger'">{{ d.decision === 1 ? 'ALLOW' : 'DENY' }}</span></td>
            <td><span class="tag">{{ d.channel === 1 ? 'remote' : 'local' }}</span></td>
            <td class="mono">{{ d.latency_ms }}ms</td>
            <td class="mono text-secondary" style="white-space: nowrap;">{{ formatTime(d.created_at) }}</td>
          </tr>
        </tbody>
      </table>
      <div v-if="decisions.length === 0" class="empty-state">暂无决策记录</div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { api } from '../api/client'

const route = useRoute()
const router = useRouter()

const tab = ref<string>((route.query.tab as string) || 'requests')
const myRequests = ref<any[]>([])
const pendingApprovals = ref<any[]>([])
const doneApprovals = ref<any[]>([])
const publishes = ref<any>({})
const audit = ref<any[]>([])
const decisions = ref<any[]>([])

function setTab(t: string) {
  tab.value = t
  router.replace({ query: { tab: t } })
  load()
}

function formatTime(t: string) {
  if (!t) return '—'
  try { return new Date(t).toLocaleString('zh-CN') } catch { return t }
}

async function load() {
  try {
    if (tab.value === 'requests') {
      myRequests.value = ((await api.auditMyRequests()) as any).items || []
    } else if (tab.value === 'approvals') {
      const d = (await api.auditMyApprovals()) as any
      pendingApprovals.value = d.pending || []
      doneApprovals.value = d.done || []
    } else if (tab.value === 'publishes') {
      publishes.value = await api.auditMyPublishes()
    } else if (tab.value === 'audit') {
      audit.value = ((await api.auditLogs()) as any).items || []
    } else if (tab.value === 'decision') {
      decisions.value = ((await api.decisionLogs()) as any).items || []
    }
  } catch { /* partial */ }
}

async function approve(id: number, action: number) {
  try {
    const res: any = await api.approveRequest(id, action, action === 1 ? '同意' : '驳回')
    if (res && res.status === 'partially_approved') {
      ElMessage.info(`已通过，尚待 ${(res.remaining || []).length} 位审批人（被授权方确认 / 其他负责人复核）`)
    } else if (res && res.status === 'approved') {
      ElMessage.success('审批链全部通过，权限已自动生效')
    } else if (action === 2) {
      ElMessage.success('已驳回')
    }
    load()
  } catch (e: any) {
    ElMessage.error(e.message)
  }
}

function subjectText(r: any): string {
  const map: any = { 1: '用户', 2: '组', 3: '组织', 4: '服务' }
  const t = map[r.applicant_subject_type] || '用户'
  return `${t}#${r.applicant_subject_id}`
}

function reqStatus(s: number): string {
  return { 0: '草稿', 1: '审批中', 2: '已通过', 3: '已驳回', 4: '已回收' }[s] || `#${s}`
}
function reqStatusClass(s: number): string {
  return { 2: 'tag-success', 3: 'tag-danger' }[s] || ''
}

onMounted(load)
</script>

<style scoped>
.audit-page { max-width: 1400px; }
.page-header { margin-bottom: 20px; }
.page-header h1 { font-size: 24px; font-weight: 700; letter-spacing: -0.5px; margin-bottom: 4px; }
.page-desc { font-size: 13px; color: var(--text-secondary); }

.tabs { display: flex; gap: 0; border: 1px solid var(--border); width: fit-content; margin-bottom: 0; }
.tab { padding: 8px 20px; font-size: 13px; font-weight: 500; background: var(--bg); border: none; border-right: 1px solid var(--border); color: var(--text-secondary); cursor: pointer; transition: all 0.15s; font-family: var(--font-mono); }
.tab:last-child { border-right: none; }
.tab:hover { background: var(--bg-hover); color: var(--text); }
.tab.active { background: var(--accent); color: var(--accent-text); font-weight: 600; }

.panel { border: 1px solid var(--border); border-top: none; background: var(--bg); }
.sub-title { font-size: 11px; font-weight: 600; text-transform: uppercase; letter-spacing: 1px; color: var(--text-secondary); font-family: var(--font-mono); padding: 12px 16px 4px; background: var(--bg-secondary); border-bottom: 1px solid var(--border); }

.data-table { width: 100%; border-collapse: collapse; font-size: 13px; }
.data-table th { text-align: left; padding: 10px 14px; font-family: var(--font-mono); font-size: 10px; font-weight: 600; text-transform: uppercase; letter-spacing: 1px; color: var(--text-secondary); background: var(--bg-secondary); border-bottom: 1px solid var(--border); }
.data-table td { padding: 9px 14px; border-bottom: 1px solid var(--border); }
.data-table tr:hover td { background: var(--bg-hover); }

.btn { padding: 4px 12px; font-size: 11px; font-weight: 600; border: 1px solid var(--border); background: var(--bg); color: var(--text); cursor: pointer; transition: all 0.15s; font-family: var(--font-mono); }
.btn:hover { background: var(--bg-hover); border-color: var(--border-strong); }
.btn-primary { background: var(--accent); color: var(--accent-text); border-color: var(--accent); }
.btn-sm { padding: 4px 12px; font-size: 11px; }

.mono { font-family: var(--font-mono); font-size: 12px; }
.text-secondary { color: var(--text-secondary); }
.tag { font-family: var(--font-mono); font-size: 10px; font-weight: 600; padding: 2px 8px; background: var(--bg-tertiary); text-transform: uppercase; letter-spacing: 0.5px; }
.tag-success { background: rgba(34, 197, 94, 0.15); color: #22c55e; }
.tag-danger { background: rgba(239, 68, 68, 0.15); color: #ef4444; }
.empty-state { padding: 32px; text-align: center; color: var(--text-tertiary); font-size: 13px; }
</style>

<style scoped>
.audit-page { max-width: 1400px; }
.page-header { margin-bottom: 20px; }
.page-header h1 { font-size: 24px; font-weight: 700; letter-spacing: -0.5px; margin-bottom: 4px; }
.page-desc { font-size: 13px; color: var(--text-secondary); }

.tabs { display: flex; gap: 0; border: 1px solid var(--border); width: fit-content; margin-bottom: 0; }
.tab { padding: 8px 20px; font-size: 13px; font-weight: 500; background: var(--bg); border: none; border-right: 1px solid var(--border); color: var(--text-secondary); cursor: pointer; transition: all 0.15s; font-family: var(--font-mono); }
.tab:last-child { border-right: none; }
.tab:hover { background: var(--bg-hover); color: var(--text); }
.tab.active { background: var(--accent); color: var(--accent-text); font-weight: 600; }

.panel { border: 1px solid var(--border); border-top: none; background: var(--bg); }

.data-table { width: 100%; border-collapse: collapse; font-size: 13px; }
.data-table th { text-align: left; padding: 10px 14px; font-family: var(--font-mono); font-size: 10px; font-weight: 600; text-transform: uppercase; letter-spacing: 1px; color: var(--text-secondary); background: var(--bg-secondary); border-bottom: 1px solid var(--border); }
.data-table td { padding: 9px 14px; border-bottom: 1px solid var(--border); }
.data-table tr:hover td { background: var(--bg-hover); }

.mono { font-family: var(--font-mono); font-size: 12px; }
.text-secondary { color: var(--text-secondary); }
.tag { font-family: var(--font-mono); font-size: 10px; font-weight: 600; padding: 2px 8px; background: var(--bg-tertiary); text-transform: uppercase; letter-spacing: 0.5px; }
.tag-success { background: var(--success-bg); }
.tag-danger { background: var(--danger-bg); }
.empty-state { padding: 32px; text-align: center; color: var(--text-tertiary); font-size: 13px; }
</style>
