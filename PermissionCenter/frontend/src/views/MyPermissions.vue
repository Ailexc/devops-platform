<template>
  <div class="my-permissions-page">
    <PageHeader title="我的权限" desc="按能力包维度查看：个人 / 组织 / 自建组 —— 每条授权都有对应申请单">
      <template #actions>
        <router-link to="/marketplace" class="btn btn-primary">＋ 申请权限</router-link>
      </template>
    </PageHeader>

    <!-- 概览统计 -->
    <div class="stats">
      <div v-for="(t, i) in TABS" :key="t.v" class="stat-card" :class="[`tone-${t.tone}`, { active: tab === t.v }]" @click="tab = t.v">
        <div class="stat-icon">{{ t.icon }}</div>
        <div>
          <div class="stat-value">{{ listOf(t.v).length }}</div>
          <div class="stat-label">{{ t.label }}</div>
        </div>
      </div>
    </div>

    <div class="dim-title">{{ activeLabel }} <span class="dim-count">{{ listOf(tab).length }} 项能力包授权</span></div>

    <div v-if="listOf(tab).length === 0" class="empty-state">该维度暂无能力包授权</div>
    <div v-else class="cap-grid">
      <div v-for="(p, i) in listOf(tab)" :key="p.request_id + '-' + i" class="cap-card" @click="openDetail(p)">
        <div class="cap-top">
          <div class="cap-icon" :class="toneOf(p)">{{ iconOf(p) }}</div>
          <div style="flex:1;min-width:0;">
            <div class="cap-name">{{ p.capability_name }}</div>
            <div class="cap-app">{{ p.app_name }} · <span class="mono">{{ p.preset_name }}</span></div>
          </div>
          <span class="tag tag-ok">已生效</span>
        </div>
        <div class="cap-desc">{{ p.description || '—' }}</div>
        <div class="cap-tags">
          <span class="tag" :class="dimTag(p.grantee_type)">{{ DIM[p.grantee_type] || p.grantee_type }}</span>
          <span v-if="p.scope_text" class="tag tag-cyan">范围: {{ p.scope_text }}</span>
          <span class="tag tag-gray">{{ (p.interfaces || []).length }} 接口</span>
        </div>
        <div class="cap-foot">
          <span class="foot-time">{{ p.created_at }}</span>
          <span class="foot-link">查看详情 →</span>
        </div>
      </div>
    </div>

    <!-- 能力包详情 + 申请单缩略 抽屉 -->
    <el-drawer v-model="showDrawer" :title="current?.capability_name || '能力包详情'" size="480px">
      <div v-if="current" class="detail-view">
        <div class="dv-head">
          <div class="cap-icon big" :class="toneOf(current)">{{ iconOf(current) }}</div>
          <div style="flex:1;">
            <div class="dv-name">{{ current.capability_name }}</div>
            <div class="dv-app">{{ current.app_name }} · <span class="mono">{{ current.preset_name }}</span></div>
          </div>
          <span class="tag tag-ok">已生效</span>
        </div>
        <p class="dv-desc">{{ current.description || '—' }}</p>

        <div class="sec">
          <div class="sec-title">📦 能力包详情</div>
          <div class="kv"><span class="k">所属应用</span><span class="v">{{ current.app_name }}</span></div>
          <div class="kv"><span class="k">权限预设</span><span class="v mono">{{ current.preset_name }}</span></div>
          <div class="kv"><span class="k">作用主体</span><span class="v">{{ DIM[current.grantee_type] || current.grantee_type }} · {{ current.grantee_name }}</span></div>
          <div class="kv"><span class="k">数据范围</span><span class="v">{{ current.scope_text || '接口级（全部数据）' }}</span></div>
          <div class="kv"><span class="k">授权时间</span><span class="v mono">{{ current.created_at }}</span></div>
          <div class="kv"><span class="k">接口权限</span><span class="v"><span v-for="op in current.interfaces || []" :key="op" class="op-chip mono">{{ op }}</span></span></div>
        </div>

        <div class="sec">
          <div class="sec-title">📋 申请单</div>
          <div v-if="reqDetail">
            <div class="req-head">
              <span class="tag tag-blue">{{ reqDetail.request.request_type === 3 ? '接入申请' : '权限申请' }}</span>
              <span class="req-title">{{ reqDetail.title }}</span>
              <span class="tag" :class="reqDetail.request.status === 2 ? 'tag-ok' : 'tag-amber'">{{ statusLabel(reqDetail.request.status) }}</span>
              <span class="req-link" @click="gotoRequest">完整单 →</span>
            </div>
            <div class="kv"><span class="k">单号</span><span class="v mono req-no">{{ reqDetail.ticket_no }}</span></div>
            <div class="kv"><span class="k">风险</span><span class="v">{{ ['低', '中', '高'][reqDetail.request.risk_level - 1] || '—' }}</span></div>
            <div class="kv"><span class="k">申请人</span><span class="v">{{ reqDetail.applicant }}</span></div>
            <div class="kv"><span class="k">理由</span><span class="v reason">{{ reqDetail.request.reason || '—' }}</span></div>

            <div class="timeline">
              <div class="tl-step done">
                <div class="tl-dot"></div>
                <div>
                  <div class="tl-title">发起申请 <span class="tag tag-ok">已提交</span></div>
                  <div class="tl-meta">{{ reqDetail.applicant }} · {{ reqDetail.request.created_at }}</div>
                </div>
              </div>
              <div v-for="(task, ti) in reqDetail.tasks || []" :key="ti" class="tl-step" :class="task.action === 1 ? 'done' : task.action === 2 ? 'reject' : ''">
                <div class="tl-dot"></div>
                <div>
                  <div class="tl-title">{{ task.approver_name }} <span class="tag" :class="task.action === 1 ? 'tag-ok' : task.action === 2 ? 'tag-amber' : 'tag-gray'">{{ task.action === 1 ? '通过' : task.action === 2 ? '拒绝' : '待审批' }}</span></div>
                  <div class="tl-meta">{{ task.approver_role }} · {{ task.updated_at }}</div>
                </div>
              </div>
            </div>

            <div class="sec-sub">权限表达式</div>
            <div class="expr-toggle" @click="showExpr = !showExpr">{{ showExpr ? '收起表达式 ▴' : '展开表达式 ▾' }}</div>
            <div v-if="showExpr" class="expr">{{ reqDetail.request.content?.scope_expression || '—' }}</div>
          </div>
          <div v-else class="text-secondary" style="font-size:12px;">加载申请单…</div>
        </div>

        <div class="footer-actions">
          <button class="btn" @click="gotoMarket">📦 查看能力包</button>
          <!-- 管理能力包按钮改为打开弹窗 -->
          <button class="btn btn-primary" @click="openManageDialog">⚙️ 管理能力包</button>
        </div>
      </div>
    </el-drawer>

    <CapabilityManageDialog
      v-model="showManageDialog"
      :capability-id="manageCapabilityId"
      @refresh="loadData"
    />
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { api } from '../api/client'
import { ElMessage, ElMessageBox } from 'element-plus'
import PageHeader from '../components/PageHeader.vue'
import CapabilityManageDialog from '../components/CapabilityManageDialog.vue'

const TABS = [
  { v: 'personal', label: '个人权限', icon: '👤', tone: 'blue' },
  { v: 'org', label: '组织权限', icon: '🏢', tone: 'violet' },
  { v: 'group', label: '自建组权限', icon: '👥', tone: 'amber' },
]
const DIM: Record<string, string> = { user: '👤 个人', org: '🏢 组织', group: '👥 自建组', app: '🔌 程序' }

const router = useRouter()
const tab = ref('personal')
const data = ref<any>({ personal: [], org: [], group: [] })
const showDrawer = ref(false)
const current = ref<any>(null)
const reqDetail = ref<any>(null)
const showExpr = ref(false)
const showManageDialog = ref(false)
const manageCapabilityId = ref(0)

function listOf(v: string) {
  return data.value?.[v] || []
}
const activeLabel = computed(() => TABS.find(t => t.v === tab.value)?.label || '权限')
function iconOf(p: any) {
  const n = p.capability_name || ''
  if (n.includes('主机')) return '🖥️'
  if (n.includes('数据库')) return '🗄️'
  if (n.includes('容器')) return '🐳'
  if (n.includes('安全')) return '🛡️'
  if (n.includes('路由')) return '🧭'
  if (n.includes('权限')) return '🔑'
  if (n.includes('服务')) return '🧩'
  if (n.includes('环境')) return '🌍'
  return '📦'
}
function toneOf(p: any) {
  const n = p.capability_name || ''
  if (n.includes('主机')) return 'blue'
  if (n.includes('数据库')) return 'amber'
  if (n.includes('容器')) return 'cyan'
  if (n.includes('权限')) return 'violet'
  return 'green'
}
function dimTag(t: string) {
  return { user: 'tag-blue', org: 'tag-violet', group: 'tag-amber' }[t] || 'tag-gray'
}
function statusLabel(s: number) {
  return ['', '待审批', '已通过', '已拒绝', '已回收'][s] || s
}

async function openDetail(p: any) {
  current.value = p
  reqDetail.value = null
  showDrawer.value = true
  try {
    reqDetail.value = await api.requestDetail(p.request_id)
  } catch { /* ignore */ }
}

function gotoRequest() {
  if (reqDetail.value) {
    router.push(`/requests/${reqDetail.value.request.id}`)
  }
}

function gotoMarket() {
  if (current.value) {
    router.push(`/marketplace?capability=${current.value.capability_id}`)
  }
}

function openManageDialog() {
  manageCapabilityId.value = current.value?.capability_id || 0
  showManageDialog.value = true
}

async function loadData() {
  try {
    data.value = await api.meCapabilityPermissions()
  } catch (e: any) {
    ElMessage.error(e.message || '加载失败')
  }
}

onMounted(loadData)
</script>

<style scoped>
.my-permissions-page { padding: 0 24px 40px; }
.stats { display: flex; gap: 16px; margin-bottom: 20px; }
.stat-card { flex: 1; display: flex; align-items: center; gap: 14px; padding: 18px 20px; border-radius: 14px; border: 2px solid var(--border); background: var(--bg-card); cursor: pointer; transition: all .2s; }
.stat-card:hover, .stat-card.active { border-color: var(--brand); background: var(--brand-soft); }
.stat-card.tone-blue { --accent: var(--brand); }
.stat-card.tone-violet { --accent: var(--purple); }
.stat-card.tone-amber { --accent: var(--warning); }
.stat-card.tone-cyan { --accent: var(--info); }
.stat-card.tone-green { --accent: var(--success); }
.stat-icon { font-size: 28px; }
.stat-value { font-size: 28px; font-weight: 800; line-height: 1; }
.stat-label { font-size: 12px; color: var(--text-tertiary); margin-top: 2px; }
.dim-title { font-size: 15px; font-weight: 700; margin-bottom: 14px; }
.dim-count { font-weight: 400; color: var(--text-tertiary); font-size: 13px; }
.cap-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(320px, 1fr)); gap: 16px; }
.cap-card { border: 1px solid var(--border); border-radius: 14px; padding: 18px; background: var(--bg-card); cursor: pointer; transition: box-shadow .2s, border-color .2s, transform .2s; }
.cap-card:hover { border-color: var(--brand); box-shadow: var(--shadow-md); transform: translateY(-2px); }
.cap-top { display: flex; align-items: center; gap: 12px; margin-bottom: 10px; }
.cap-icon { width: 44px; height: 44px; border-radius: 12px; display: flex; align-items: center; justify-content: center; font-size: 20px; flex-shrink: 0; }
.cap-icon.blue { background: var(--brand-soft); }
.cap-icon.amber { background: var(--warning-bg); }
.cap-icon.cyan { background: var(--info-bg); }
.cap-icon.violet { background: var(--purple-bg); }
.cap-icon.green { background: var(--success-bg); }
.cap-icon.big { width: 52px; height: 52px; font-size: 24px; }
.cap-name { font-size: 16px; font-weight: 700; }
.cap-app { font-size: 12px; color: var(--text-tertiary); margin-top: 2px; }
.cap-desc { font-size: 13px; color: var(--text-secondary); margin-bottom: 12px; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden; }
.cap-tags { display: flex; gap: 6px; flex-wrap: wrap; }
.cap-foot { display: flex; align-items: center; justify-content: space-between; margin-top: 14px; padding-top: 12px; border-top: 1px solid var(--border); }
.foot-time { font-size: 12px; color: var(--text-tertiary); }
.foot-link { font-size: 13px; color: var(--brand); font-weight: 600; }
.tag { font-family: var(--font-mono); font-size: 10px; font-weight: 600; padding: 2px 8px; border-radius: 999px; }
.tag-ok { background: var(--success-bg); color: var(--success); }
.tag-amber { background: var(--warning-bg); color: var(--warning); }
.tag-cyan { background: var(--info-bg); color: var(--info); }
.tag-blue { background: var(--brand-soft); color: var(--brand-strong); }
.tag-violet { background: var(--purple-bg); color: var(--purple); }
.tag-gray { background: var(--bg-inset); color: var(--text-tertiary); border: 1px solid var(--border); }
.empty-state { padding: 60px; text-align: center; color: var(--text-tertiary); font-size: 13px; }
.mono { font-family: var(--font-mono); font-size: 12px; }
.text-secondary { color: var(--text-secondary); }

/* 抽屉 */
.detail-view { padding: 0 4px; }
.dv-head { display: flex; align-items: center; gap: 12px; margin-bottom: 12px; }
.dv-name { font-size: 17px; font-weight: 700; }
.dv-app { font-size: 12px; color: var(--text-tertiary); }
.dv-desc { font-size: 13px; color: var(--text-secondary); margin-bottom: 18px; line-height: 1.7; }
.sec { margin-bottom: 18px; }
.sec-title { font-size: 13px; font-weight: 700; margin-bottom: 8px; color: var(--text); }
.sec-sub { font-size: 11px; font-weight: 600; color: var(--text-tertiary); text-transform: uppercase; letter-spacing: .05em; margin: 10px 0 6px; }
.kv { display: flex; gap: 10px; padding: 6px 0; font-size: 13px; border-bottom: 1px dashed var(--border); }
.k { flex: 0 0 76px; color: var(--text-tertiary); }
.v { flex: 1; word-break: break-all; }
.reason { color: var(--text-secondary); }
.expr { font-size: 11px; color: var(--info); white-space: pre-wrap; background: var(--bg-inset); border: 1px solid var(--border); border-radius: 6px; padding: 6px; }
.op-chip { display: inline-block; padding: 2px 6px; margin: 2px; background: var(--bg-inset); border: 1px solid var(--border); border-radius: 4px; font-size: 11px; }
.req-head { display: flex; align-items: center; gap: 8px; padding: 8px 10px; background: var(--bg-inset); border: 1px solid var(--border); border-radius: 8px; margin-bottom: 8px; flex-wrap: wrap; }
.req-title { font-size: 13px; font-weight: 600; flex: 1; min-width: 120px; }
.req-no { font-weight: 700; color: var(--brand-strong); }
.req-link { font-size: 12px; color: var(--brand); cursor: pointer; font-weight: 600; }
.req-link:hover { text-decoration: underline; }
.timeline { border-left: 2px solid var(--border); padding-left: 14px; margin: 10px 0; }
.tl-step { display: flex; gap: 10px; padding: 7px 0; position: relative; }
.tl-dot { width: 10px; height: 10px; border-radius: 50%; background: var(--border-strong); margin-top: 5px; flex-shrink: 0; }
.tl-step.done .tl-dot { background: var(--success); }
.tl-step.reject .tl-dot { background: var(--danger); }
.tl-title { font-size: 12px; font-weight: 600; display: flex; align-items: center; gap: 6px; }
.tl-meta { font-size: 11px; color: var(--text-tertiary); }
.expr-toggle { font-size: 12px; color: var(--brand); cursor: pointer; font-weight: 600; margin-top: 8px; }
.footer-actions { display: flex; gap: 10px; }
.footer-actions .btn { flex: 1; }
.btn { display: inline-flex; align-items: center; justify-content: center; gap: 6px; height: 36px; padding: 0 16px; border-radius: 8px; font-size: 13px; font-weight: 600; border: 1px solid var(--border); background: var(--bg-card); color: var(--text); cursor: pointer; text-decoration: none; }
.btn:hover { background: var(--bg-hover); }
.btn-primary { background: var(--brand); color: #fff; border-color: var(--brand); }
</style>
