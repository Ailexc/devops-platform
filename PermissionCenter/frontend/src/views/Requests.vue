<template>
  <div class="requests-page">
    <PageHeader title="审批中心" desc="按工单类型查看与处理：权限申请 · 接入申请 · 上架/下架 · 授权回收">
      <template #actions>
        <div class="seg">
          <button class="seg-btn" :class="{ on: role === 'applicant' }" @click="role = 'applicant'; load()">我发起的</button>
          <button class="seg-btn" :class="{ on: role === 'approver' }" @click="role = 'approver'; load()">待我审批</button>
        </div>
      </template>
    </PageHeader>

    <div class="panel explain-card">
      <div class="ex-title">🏭 真实场景说明</div>
      <div class="ex-body">生产环境：申请/上架/回收均会<b>发起到公司工单平台（OA / ITSM）</b>，本系统透传查询外部工单状态，避免用户两头跑；当前为<b>内部模拟</b>（已预留 webhook 接口）。</div>
    </div>

    <div class="tabs">
      <button v-for="t in TYPES" :key="t.v" class="tab" :class="{ active: type === t.v }" @click="type = t.v; load()">
        {{ t.label }} <span class="count" v-if="counts[t.v]">{{ counts[t.v] }}</span>
      </button>
    </div>

    <div class="panel">
      <table v-if="items.length" class="data-table">
        <thead><tr><th>工单号</th><th>类型</th><th>内容</th><th>授权主体</th><th>状态</th><th>风险</th><th>发起人</th><th>时间</th><th>操作</th></tr></thead>
        <tbody>
          <tr v-for="t in items" :key="t.type + t.id">
            <td class="mono">{{ t.ticket_no }}</td>
            <td><span class="tag" :class="typeTag(t.type)">{{ t.title }}</span></td>
            <td class="text-secondary" style="max-width:200px;">{{ t.sub }}</td>
            <td>
              <template v-if="t.grantee_type">
                <span class="tag" :class="granteeTag(t.grantee_type)">{{ granteeIcon(t.grantee_type) }} {{ granteeLabel(t.grantee_type) }}</span>
                <div class="mono text-secondary" style="font-size:11px;margin-top:2px;">{{ t.grantee_name }}</div>
              </template>
              <span v-else class="text-secondary">—</span>
            </td>
            <td><span class="tag" :class="statusTag(t.status)">{{ t.status }}</span></td>
            <td class="mono">{{ t.risk || '—' }}</td>
            <td>{{ t.requester || '—' }}</td>
            <td class="mono text-secondary">{{ t.created_at }}</td>
            <td>
              <router-link v-if="t.route" :to="t.route" class="btn btn-sm">详情</router-link>
              <button v-if="role === 'approver' && canApprove(t)" class="btn btn-sm btn-primary" @click="approve(t)">✅ 通过</button>
              <button v-if="role === 'approver' && canApprove(t)" class="btn btn-sm" @click="reject(t)">驳回</button>
            </td>
          </tr>
        </tbody>
      </table>
      <EmptyState v-else text="暂无工单" />
    </div>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { api, request } from '../api/client'
import { ElMessage } from 'element-plus'
import PageHeader from '../components/PageHeader.vue'
import EmptyState from '../components/EmptyState.vue'

const TYPES = [
  { v: 'all', label: '全部' },
  { v: 'apply', label: '权限申请' },
  { v: 'onboard', label: '接入申请' },
  { v: 'publish', label: '上架 / 下架' },
  { v: 'revoke', label: '授权回收' },
]
const type = ref('all')
const role = ref<'applicant' | 'approver'>('applicant')
const items = ref<any[]>([])
const counts = ref<Record<string, number>>({})

function typeTag(t: string) {
  return { apply: 'tag-blue', onboard: 'tag-violet', publish: 'tag-amber', revoke: 'tag-red' }[t] || 'tag-gray'
}
function statusTag(s: string) {
  if (s === '已通过' || s === '已完成') return 'tag-ok'
  if (s === '待审批' || s === '已发起' || s === '草稿') return 'tag-amber'
  if (s === '已拒绝' || s === '已驳回') return 'tag-red'
  return 'tag-gray'
}
function granteeTag(t: string) {
  return { user: 'tag-blue', org: 'tag-violet', group: 'tag-green', app: 'tag-amber' }[t] || 'tag-gray'
}
function granteeIcon(t: string) {
  return { user: '👤', org: '🏢', group: '👥', app: '🔌' }[t] || '❓'
}
function granteeLabel(t: string) {
  return { user: '用户', org: '组织', group: '组', app: '程序' }[t] || t
}
function canApprove(t: any) {
  return (t.type === 'apply' || t.type === 'onboard') && t.status === '待审批' && !!t.route
}

async function approve(t: any) {
  try {
    await api.approveRequest(Number(t.route.split('/').pop()), 1, '同意')
    ElMessage.success('已通过')
    await load()
    notifyPendingChanged()
  } catch (e: any) { ElMessage.error(e.message) }
}
async function reject(t: any) {
  try {
    await api.approveRequest(Number(t.route.split('/').pop()), 2, '驳回')
    ElMessage.success('已驳回')
    await load()
    notifyPendingChanged()
  } catch (e: any) { ElMessage.error(e.message) }
}

async function load() {
  try {
    const r: any = await request(`/api/v1/tickets?type=${type.value}&role=${role.value}`)
    items.value = r.items || []
    // 各类型计数：跟随当前角色（我发起=我发起的；待我审批=待我处理的待办）
    const all: any = await request(`/api/v1/tickets?type=all&role=${role.value}`)
    const c: Record<string, number> = {}
    for (const t of TYPES) if (t.v !== 'all') c[t.v] = (all.items || []).filter((x: any) => x.type === t.v).length
    counts.value = c
  } catch (e: any) { ElMessage.error(e.message) }
}

// 审批动作后通知侧栏刷新待审批红点
function notifyPendingChanged() {
  window.dispatchEvent(new CustomEvent('iam:pending-changed'))
}

onMounted(load)
</script>

<style scoped>
.seg { display: flex; border: 1px solid var(--border); border-radius: 8px; overflow: hidden; }
.seg-btn { padding: 6px 14px; font-size: 12px; font-weight: 600; background: var(--bg-card); border: none; border-right: 1px solid var(--border); color: var(--text-secondary); cursor: pointer; }
.seg-btn:last-child { border-right: none; }
.seg-btn.on { background: var(--brand-soft); color: var(--brand-strong); }
.explain-card { display: flex; gap: 16px; align-items: flex-start; background: var(--brand-softer); border-color: rgba(47,111,237,.25); }
.ex-title { font-size: 13px; font-weight: 700; color: var(--brand-strong); white-space: nowrap; }
.ex-body { font-size: 12px; color: var(--text-secondary); }
.tabs { display: flex; gap: 0; border: 1px solid var(--border); border-radius: 8px; width: fit-content; overflow: hidden; margin-bottom: 12px; }
.tab { padding: 8px 18px; font-size: 13px; font-weight: 500; background: var(--bg-card); border: none; border-right: 1px solid var(--border); color: var(--text-secondary); cursor: pointer; }
.tab:last-child { border-right: none; }
.tab.active { background: var(--brand-soft); color: var(--brand-strong); font-weight: 600; }
.count { display: inline-flex; align-items: center; justify-content: center; min-width: 18px; height: 18px; border-radius: 999px; background: var(--brand); color: #fff; font-size: 10px; margin-left: 4px; padding: 0 4px; }
.panel { background: var(--bg-card); border: 1px solid var(--border); border-radius: var(--radius); padding: 16px; margin-bottom: 14px; box-shadow: var(--shadow-sm); }
.data-table { width: 100%; border-collapse: collapse; font-size: 13px; }
.data-table th { text-align: left; padding: 8px 12px; font-family: var(--font-mono); font-size: 10px; text-transform: uppercase; color: var(--text-secondary); background: var(--bg-secondary); border-bottom: 1px solid var(--border); }
.data-table td { padding: 8px 12px; border-bottom: 1px solid var(--border); }
.tag { font-family: var(--font-mono); font-size: 10px; font-weight: 600; padding: 2px 8px; border-radius: 999px; }
.tag-ok { background: var(--success-bg); color: var(--success); }
.tag-amber { background: var(--warning-bg); color: var(--warning); }
.tag-red { background: var(--danger-bg); color: var(--danger); }
.tag-blue { background: var(--brand-soft); color: var(--brand-strong); }
.tag-violet { background: var(--purple-bg); color: var(--purple); }
.tag-green { background: rgba(16,185,129,.12); color: #059669; }
.tag-gray { background: var(--bg-inset); color: var(--text-tertiary); border: 1px solid var(--border); }
.btn { display: inline-flex; align-items: center; gap: 5px; height: 30px; padding: 0 12px; border-radius: 8px; font-size: 12px; font-weight: 600; border: 1px solid var(--border); background: var(--bg-card); color: var(--text); cursor: pointer; text-decoration: none; margin-right: 6px; }
.btn:hover { background: var(--bg-hover); }
.btn-primary { background: var(--brand); color: #fff; border-color: var(--brand); }
.btn-sm { font-size: 12px; }
.mono { font-family: var(--font-mono); font-size: 12px; }
.text-secondary { color: var(--text-secondary); }
</style>
