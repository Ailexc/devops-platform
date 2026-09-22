<template>
  <div class="requests-page">
    <PageHeader title="审批中心" desc="按工单类型查看与处理：权限申请 · 接入申请 · 上架/下架 · 授权回收 · 定制需求">
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
              <button v-if="role === 'approver' && t.type === 'custom' && t.status === '待审批'" class="btn btn-sm btn-primary" @click="openFulfill(t)">🧩 处置</button>
              <button v-if="role === 'approver' && canApprove(t)" class="btn btn-sm" @click="reject(t)">驳回</button>
            </td>
          </tr>
        </tbody>
      </table>
      <EmptyState v-else text="暂无工单" />
    </div>

    <!-- A8 处置弹窗：直授（强制 TTL 到期回收）/ 转为能力包（造包信号） -->
    <div v-if="fulfill.open" class="modal-mask" @click.self="fulfill.open = false">
      <div class="modal-card">
        <div class="modal-head"><b>🧩 处置定制需求 {{ fulfill.t?.ticket_no }}</b>
          <button class="modal-x" @click="fulfill.open = false">✕</button></div>
        <p class="modal-hint">申请人：<b>{{ fulfill.t?.requester }}</b> —— {{ fulfill.t?.sub }}</p>
        <div class="fulfill-modes">
          <button class="fm" :class="{ on: fulfill.mode === 'grant' }" @click="fulfill.mode = 'grant'">
            <b>⚡ 直接授权</b><span>立即生效；强制带 TTL、到期自动判定排除并回收（不留游离授权碎片）</span></button>
          <button class="fm" :class="{ on: fulfill.mode === 'package' }" @click="fulfill.mode = 'package'">
            <b>📦 转为能力包</b><span>诉求有普适性 → 线下补包上架，申请人走正常申请（高频定制=造包信号）</span></button>
        </div>
        <label v-if="fulfill.mode === 'grant'" class="modal-label">有效期 TTL（天，1-365，必填）
          <input type="number" v-model.number="fulfill.ttl" min="1" max="365" class="m-input" />
        </label>
        <label class="modal-label">处置备注（留痕）
          <input v-model="fulfill.note" class="m-input" placeholder="如：按诉求直授 / 已排期补包" />
        </label>
        <div class="modal-foot">
          <button class="btn" @click="fulfill.open = false">取消</button>
          <button class="btn btn-primary" @click="submitFulfill">确认处置</button>
        </div>
      </div>
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
  { v: 'custom', label: '定制需求' }, // A8 非目录请求
]
const type = ref('all')
const role = ref<'applicant' | 'approver'>('applicant')
const items = ref<any[]>([])
const counts = ref<Record<string, number>>({})

function typeTag(t: string) {
  return { apply: 'tag-blue', onboard: 'tag-violet', publish: 'tag-amber', revoke: 'tag-red', custom: 'tag-green' }[t] || 'tag-gray'
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

// ---- A8 定制需求处置（grant 直授带 TTL / package 转为能力包）----
const fulfill = ref<{ open: boolean; t: any; mode: 'grant' | 'package'; ttl: number; note: string }>(
  { open: false, t: null, mode: 'grant', ttl: 1, note: '' })

function openFulfill(t: any) {
  fulfill.value = { open: true, t, mode: 'grant', ttl: 1, note: '' }
}
async function submitFulfill() {
  const f = fulfill.value
  if (!f.t) return
  if (f.mode === 'grant' && (!f.ttl || f.ttl < 1 || f.ttl > 365)) {
    ElMessage.error('TTL 天数须在 1-365（直授必须带有效期）')
    return
  }
  try {
    const rid = Number(f.t.route.split('/').pop())
    const r: any = await api.fulfillRequest(rid, {
      mode: f.mode, ttl_days: f.mode === 'grant' ? f.ttl : 0, note: f.note,
    })
    ElMessage.success(f.mode === 'grant'
      ? `已直接授权（TTL ${f.ttl} 天，到期自动回收）：策略 #${r.policy_id}`
      : '已标记转为能力包——请线下补包上架后通知申请人走正常流程')
    fulfill.value.open = false
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
/* ---- A8 处置弹窗 ---- */
.modal-mask { position: fixed; inset: 0; background: rgba(15, 23, 42, .45); display: flex; align-items: center; justify-content: center; z-index: 100; }
.modal-card { width: 460px; max-width: 92vw; background: var(--bg-card); border: 1px solid var(--border); border-radius: 12px; padding: 20px; box-shadow: 0 18px 48px rgba(15, 23, 42, .22); }
.modal-head { display: flex; align-items: center; justify-content: space-between; font-size: 15px; margin-bottom: 8px; }
.modal-x { border: none; background: none; font-size: 16px; cursor: pointer; color: var(--text-secondary); }
.modal-hint { font-size: 12px; color: var(--text-secondary); line-height: 1.6; margin: 0 0 12px; }
.modal-label { display: flex; flex-direction: column; gap: 5px; font-size: 13px; font-weight: 600; margin-bottom: 12px; }
.m-input { width: 100%; padding: 8px 10px; border: 1px solid var(--border); border-radius: 8px; background: var(--bg-card); color: var(--text); font-size: 13px; font-family: inherit; }
.m-input:focus { outline: none; border-color: var(--brand); }
.fulfill-modes { display: flex; flex-direction: column; gap: 8px; margin-bottom: 12px; }
.fm { display: flex; flex-direction: column; gap: 3px; align-items: flex-start; text-align: left; padding: 10px 12px; border: 1px solid var(--border); border-radius: 10px; background: var(--bg-card); cursor: pointer; transition: all .15s; }
.fm span { font-size: 11px; color: var(--text-secondary); line-height: 1.5; }
.fm.on { border-color: var(--brand); background: var(--brand-soft); }
.modal-foot { display: flex; align-items: center; gap: 10px; justify-content: flex-end; margin-top: 8px; }
.btn-sm { font-size: 12px; }
.mono { font-family: var(--font-mono); font-size: 12px; }
.text-secondary { color: var(--text-secondary); }
</style>
