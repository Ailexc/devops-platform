<template>
  <div class="cap-authz" v-if="data">
    <header class="page-header">
      <router-link :to="`/apps/${appId}`" class="back-link">← 返回应用详情</router-link>
      <h1>
        <span class="mono">{{ data.capability?.name }}</span>
        <span class="tag tag-info">授权管理</span>
      </h1>
      <span class="page-desc">{{ appName }} · {{ data.capability?.description }}</span>
    </header>

    <div class="panel info-box">🔑 <b>统一管理</b>：每个预设可单独<b>上架/下架</b>，可展开查看<b>授权信息</b>；也可以下架整个能力包。上架/下架均需走审批（发起到工单）。</div>

    <!-- ① 预设管理 -->
    <div class="section-title">① 预设管理（状态 + 上架/下架 + 授权信息）
      <span class="text-secondary">已上架 {{ publishedCount }} / 草稿 {{ draftCount }}</span>
    </div>
    <div class="panel">
      <div v-for="(p, i) in data.presets" :key="p.id" class="preset-row" :class="{ open: openPreset === p.id }">
        <div class="preset-head">
          <span class="preset-idx">{{ i + 1 }}</span>
          <b>{{ p.name }}</b>
          <span class="tag" :class="p.status === 'published' ? 'tag-ok' : 'tag-warn'">{{ p.status === 'published' ? '已上架' : '草稿' }}</span>
          <span class="badge mono">{{ granteeLabel(p.grantee_types) }}</span>
          <span class="text-secondary" style="font-size:11px;">接口 {{ (p.interfaces || []).length }} · 被授权 {{ statsOf(p.id).total }}</span>
          <span style="margin-left:auto;"></span>
          <button v-if="p.status === 'draft'" class="btn btn-sm btn-primary" @click="openPublish(p, 'publish')">🚀 上架</button>
          <button v-else class="btn btn-sm" @click="openPublish(p, 'offline')">📉 下架</button>
          <button class="btn btn-sm" @click="togglePreset(p.id)">{{ openPreset === p.id ? '收起' : '🔑 授权信息' }}</button>
        </div>
        <div class="preset-ops">
          <span v-for="op in p.interfaces" :key="op" class="op-item mono">{{ op }}</span>
        </div>
        <div v-if="openPreset === p.id" class="grant-body">
          <table v-if="grantsOf(p.id).length" class="data-table data-table-sm">
            <thead><tr><th>维度</th><th>主体</th><th>申请单</th><th>授权时间</th></tr></thead>
            <tbody>
              <tr v-for="(g, gi) in grantsOf(p.id)" :key="gi">
                <td><span class="mono">{{ g.dim }}</span></td>
                <td><b>{{ g.name }}</b><div class="mono text-secondary">{{ g.sub }}</div></td>
                <td><span class="mono" @click="gotoRequest(g.req_id)" style="cursor:pointer;color:var(--accent);">REQ-{{ String(g.req_id).padStart(4, '0') }}</span></td>
                <td><span class="mono text-secondary">{{ g.time }}</span></td>
              </tr>
            </tbody>
          </table>
          <div v-else class="empty-state">该预设暂无被授权主体</div>
        </div>
      </div>
    </div>

    <!-- ② 能力包整体操作 -->
    <div class="section-title">② 能力包整体操作</div>
    <div class="panel">
      <div class="btn-row">
        <button class="btn btn-primary btn-sm" @click="batchPublish" :disabled="draftCount === 0">🚀 上架全部草稿预设（{{ draftCount }}）</button>
        <button class="btn btn-sm btn-danger" @click="offlineAll">📉 下架整个能力包（全部 {{ data.presets.length }} 个预设）</button>
      </div>
    </div>

    <!-- ③ 授权概况 -->
    <div class="section-title">③ 授权概况
      <span class="text-secondary">全部预设 · 被授权主体总数 {{ data.grants?.total }}</span>
    </div>
    <div class="panel">
      <table class="data-table data-table-sm">
        <thead><tr><th>预设</th><th>状态</th><th>用户</th><th>组织</th><th>自建组</th><th>程序</th><th>合计</th></tr></thead>
        <tbody>
          <tr v-for="p in data.presets" :key="p.id">
            <td><b>{{ p.name }}</b></td>
            <td><span class="tag" :class="p.status === 'published' ? 'tag-ok' : 'tag-warn'">{{ p.status === 'published' ? '已上架' : '草稿' }}</span></td>
            <td class="mono">{{ statsOf(p.id).user }}</td>
            <td class="mono">{{ statsOf(p.id).org }}</td>
            <td class="mono">{{ statsOf(p.id).group }}</td>
            <td class="mono">{{ statsOf(p.id).app }}</td>
            <td class="mono"><b>{{ statsOf(p.id).total }}</b></td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- 上架 / 下架 审批弹窗 -->
    <el-dialog v-model="showModal" :title="modalTitle" width="560">
      <div v-if="modalTarget" class="flow">
        <div class="flow-step" :class="{ active: true }">
          <div class="step-title">发起{{ modalAction === 'publish' ? '上架' : '下架' }}</div>
          <div class="step-desc">{{ modalTarget.name }} · {{ (modalTarget.interfaces || []).length }} 接口</div>
        </div>
        <div class="flow-step">
          <div class="step-title">应用 Owner 确认</div>
          <div class="step-desc">{{ appName }} 负责人</div>
        </div>
        <div class="flow-step">
          <div class="step-title">平台复核</div>
          <div class="step-desc">效能平台 · 安全合规</div>
        </div>
        <div class="flow-step">
          <div class="step-title">发起到工单 · {{ modalAction === 'publish' ? '上架市场' : '撤销授权' }}</div>
          <div class="step-desc">{{ modalAction === 'publish' ? '审批通过后自动上架' : '需使用方全部审批通过后生效' }}</div>
        </div>
      </div>
      <div v-if="modalAction === 'offline'" class="warn-box">📉 下架要求 <b>{{ modalAll ? data.grants?.total : statsOf(modalTarget?.id).total }}</b> 个使用方全部审批通过后，授权才会被撤销（策略停用 + OpenFGA 关系清理）。</div>
      <div class="ticket-box">🎫 将生成{{ modalAction === 'publish' ? '上架' : '下架' }}工单 <b>WO-{{ ticketNo }}</b>（模拟）。</div>
      <template #footer>
        <button class="btn" @click="showModal = false">取消</button>
        <button class="btn" :class="modalAction === 'publish' ? 'btn-primary' : 'btn-danger'" @click="confirmModal">确认发起</button>
      </template>
    </el-dialog>
  </div>
  <div v-else class="empty-state" style="padding:60px;">加载中…</div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { api } from '../api/client'
import { ElMessage } from 'element-plus'

const route = useRoute()
const router = useRouter()
const appId = Number(route.params.id)
const cid = Number(route.params.cid)

const data = ref<any>(null)
const appName = ref('')
const openPreset = ref('')
const showModal = ref(false)
const modalTarget = ref<any>(null)
const modalAction = ref<'publish' | 'offline'>('publish')
const modalAll = ref(false)

const GRANTEE_LABEL: Record<string, string> = { user: '👤 用户', org: '🏢 组织', group: '👥 组', app: '🔌 程序' }

const publishedCount = computed(() => (data.value?.presets || []).filter((p: any) => p.status === 'published').length)
const draftCount = computed(() => (data.value?.presets || []).filter((p: any) => p.status === 'draft').length)
const ticketNo = computed(() => `20260805-0${modalAction.value === 'publish' ? '88' : '99'}`)

function granteeLabel(gts: any) {
  return (gts || []).map((g: string) => GRANTEE_LABEL[g] || g).join(' · ')
}
function statsOf(pid: string) {
  return data.value?.preset_stats?.[pid] || { user: 0, org: 0, group: 0, app: 0, total: 0 }
}
function grantsOf(pid: string) {
  return data.value?.preset_grants?.[pid] || []
}
function togglePreset(pid: string) {
  openPreset.value = openPreset.value === pid ? '' : pid
}
function openPublish(p: any, action: 'publish' | 'offline') {
  modalTarget.value = p
  modalAction.value = action
  modalAll.value = false
  showModal.value = true
}
function batchPublish() {
  modalTarget.value = null
  modalAction.value = 'publish'
  modalAll.value = true
  showModal.value = true
}
function offlineAll() {
  modalTarget.value = null
  modalAction.value = 'offline'
  modalAll.value = true
  showModal.value = true
}
async function confirmModal() {
  const body: any = { action: modalAction.value }
  if (modalAll.value) {
    body.all = true
  } else {
    body.preset_ids = [modalTarget.value.id]
  }
  try {
    await api.publishCapability(appId, cid, body)
    showModal.value = false
    ElMessage.success(modalAction.value === 'publish' ? '已发起到上架工单（模拟）→ 审批通过，预设已上架' : '已发起下架审批（模拟）：待使用方审批通过后下架生效')
    await load()
  } catch (e: any) {
    ElMessage.error(e.message)
  }
}
function gotoRequest(reqId: number) {
  router.push(`/requests/${reqId}`)
}

async function load() {
  try {
    const [authz, appDetail] = await Promise.all([api.capabilityAuthz(appId, cid), api.appDetail(appId)])
    data.value = authz
    appName.value = appDetail?.app?.name || ''
  } catch (e: any) {
    ElMessage.error(e.message)
  }
}

onMounted(load)
</script>

<style scoped>
.cap-authz { max-width: 980px; }
.page-header { margin-bottom: 18px; }
.page-header h1 { font-size: 22px; font-weight: 700; display: flex; align-items: center; gap: 10px; }
.back-link { font-size: 13px; color: var(--text-secondary); text-decoration: none; display: inline-block; margin-bottom: 6px; }
.page-desc { font-size: 12px; color: var(--text-secondary); }
.section-title { font-size: 15px; font-weight: 700; margin: 22px 0 10px; display: flex; align-items: center; gap: 10px; }
.section-title .text-secondary { font-size: 12px; font-weight: 400; }
.panel { border: 1px solid var(--border); background: var(--bg); padding: 16px; margin-bottom: 14px; }
.info-box { font-size: 12px; background: var(--bg-secondary); }
.preset-row { border: 1px solid var(--border); margin-bottom: 10px; }
.preset-row.open { border-color: var(--accent); }
.preset-head { display: flex; align-items: center; gap: 10px; padding: 12px 14px; background: var(--bg-secondary); flex-wrap: wrap; }
.preset-idx { width: 24px; height: 24px; border-radius: 50%; border: 1px solid var(--border); display: inline-flex; align-items: center; justify-content: center; font-size: 12px; font-weight: 700; }
.preset-ops { padding: 8px 14px; display: flex; gap: 6px; flex-wrap: wrap; }
.op-item { padding: 2px 6px; margin: 2px; background: var(--bg-tertiary); border: 1px solid var(--border); border-radius: 4px; font-size: 11px; }
.grant-body { padding: 10px 14px; border-top: 1px solid var(--border); }
.btn-row { display: flex; gap: 10px; }
.badge { font-size: 11px; padding: 2px 8px; background: var(--bg-tertiary); border: 1px solid var(--border); border-radius: 999px; }
.data-table { width: 100%; border-collapse: collapse; font-size: 13px; }
.data-table th { text-align: left; padding: 8px 12px; font-family: var(--font-mono); font-size: 10px; font-weight: 600; text-transform: uppercase; letter-spacing: 1px; color: var(--text-secondary); background: var(--bg-secondary); border-bottom: 1px solid var(--border); }
.data-table td { padding: 8px 12px; border-bottom: 1px solid var(--border); }
.flow { padding: 6px 0 12px; }
.flow-step { position: relative; padding: 10px 0 10px 24px; border-left: 2px solid var(--border); }
.flow-step:first-child { border-left: 2px solid var(--accent); }
.flow-step .step-title { font-size: 13px; font-weight: 600; }
.flow-step .step-desc { font-size: 11px; color: var(--text-secondary); }
.warn-box, .ticket-box { font-size: 12px; padding: 10px 12px; border: 1px solid var(--border); margin-bottom: 8px; background: var(--bg-secondary); }
.empty-state { padding: 24px; text-align: center; color: var(--text-tertiary); font-size: 13px; }
.mono { font-family: var(--font-mono); font-size: 12px; }
.text-secondary { color: var(--text-secondary); }
.tag { font-family: var(--font-mono); font-size: 10px; font-weight: 600; padding: 2px 8px; background: var(--bg-tertiary); text-transform: uppercase; letter-spacing: 0.5px; }
.tag-ok { background: rgba(34, 197, 94, 0.15); color: #22c55e; }
.tag-warn { background: rgba(245, 158, 11, 0.15); color: #d97706; }
.tag-info { background: var(--bg-tertiary); color: var(--text-secondary); }
.btn { padding: 7px 14px; font-size: 12px; font-weight: 600; border: 1px solid var(--border); background: var(--bg); color: var(--text); cursor: pointer; border-radius: var(--radius-sm); }
.btn:hover { background: var(--bg-hover); }
.btn-sm { padding: 4px 12px; font-size: 11px; }
.btn-primary { background: var(--accent); color: var(--accent-text); border-color: var(--accent); }
.btn-danger { color: #ef4444; border-color: rgba(239, 68, 68, 0.4); }
</style>
