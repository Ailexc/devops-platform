<template>
  <div class="app-market">
    <!-- 应用列表 -->
    <template v-if="!detail">
      <PageHeader title="应用市场" desc="浏览已注册应用 → 选择鉴权方式发起接入申请" />
      <div class="app-grid">
        <div v-for="a in apps" :key="a.id" class="app-card" @click="openDetail(a)">
          <div class="app-icon">{{ appIcon(a) }}</div>
          <div class="app-name">{{ a.name }}</div>
          <div class="app-meta mono">{{ a.code }} · {{ a.type === 1 ? 'API' : '数据' }}</div>
          <div class="app-tags">
            <span class="tag tag-gray">{{ capCount(a.id) }} 能力</span>
          </div>
        </div>
      </div>
      <EmptyState v-if="!apps.length" text="暂无已注册应用" />
    </template>

    <!-- 应用详情 -->
    <template v-else>
      <button class="back-link" @click="detail = null">← 返回应用市场</button>
      <PageHeader :title="`${appIcon(detail)} ${detail.name}`" :desc="`${detail.code} · ${detail.type === 1 ? 'API' : '数据'}`" />

      <div class="section-title">网络信息</div>
      <div class="panel">
        <div v-for="g in netGroups" :key="g.title" class="net-group">
          <div class="ng-title">{{ g.title }}</div>
          <div class="ng-rows">
            <div v-for="row in g.rows" :key="row.k" class="ng-row">
              <span class="ng-k">{{ row.k }}</span><span class="ng-v mono">{{ row.v }}</span>
            </div>
          </div>
        </div>
      </div>

      <div class="section-title">鉴权方式 <span class="text-tertiary">选择适合的方式发起接入申请</span></div>
      <div class="panel auth-grid">
        <div v-for="m in detail.auth || []" :key="m.type" class="auth-item">
          <div class="auth-head" @click="openAuth(m)">
            <span class="auth-icon">{{ m.icon }}</span>
            <div style="flex:1;"><div class="auth-name">{{ m.name }}</div><div class="mono text-secondary">{{ m.type }}</div></div>
            <span class="tag" :class="m.strength === 'high' ? 'tag-ok' : m.strength === 'medium' ? 'tag-warn' : ''">{{ m.strengthLabel }}</span>
          </div>
          <div class="text-secondary auth-desc">{{ m.desc }}</div>
          <div class="auth-actions">
            <span class="auth-more" @click="openAuth(m)">📖 查看运作机制</span>
            <button class="btn btn-primary btn-sm" @click.stop="openOnboardWithAuth(m)">🚀 申请此方式</button>
          </div>
        </div>
      </div>

      <!-- 产品文档（申请接入前的通俗说明入口） -->
      <template v-if="detail.doc_url">
        <div class="section-title">📖 产品文档 <span class="text-tertiary">通俗易懂的操作手册 / 使用说明</span></div>
        <div class="panel doc-panel">
          <a :href="detail.doc_url" target="_blank" rel="noopener" class="doc-link">打开 {{ detail.name }} 产品文档 →</a>
          <div class="doc-hint">接口契约之外的人可读说明，建议申请接入前先查阅。</div>
        </div>
      </template>
    </template>

    <!-- 鉴权方式全流程讲解 -->
    <AuthMethodDrawer v-model="authDrawerOpen" :method="authMethod" />

    <!-- 接入申请抽屉（从右侧滑出） -->
    <el-drawer v-model="onboardOpen" title="🔑 接入申请" size="480px" :close-on-click-modal="false">
      <div class="onboard-drawer" v-if="detail">
        <!-- 目标应用信息 -->
        <div class="od-section">
          <div class="od-label">目标应用（提供方）</div>
          <div class="od-target">
            <span class="od-icon">{{ appIcon(detail) }}</span>
            <div>
              <div class="od-name">{{ detail.name }}</div>
              <div class="od-meta mono">{{ detail.code }}</div>
            </div>
          </div>
        </div>

        <!-- 选择我的应用 -->
        <div class="od-section">
          <div class="od-label">选择我的应用（作为调用方）</div>
          <select v-model="onboard.consumer" class="input">
            <option v-for="a in meApps" :key="a.id" :value="a.id">{{ a.name }}（{{ a.code }}）</option>
          </select>
          <div v-if="!meApps.length" class="hint">你没有可用的下游应用（先注册应用后由 owner 代理申请）。</div>
          <!-- 选中应用的网络信息 -->
          <div v-if="selectedConsumerApp" class="od-consumer-info">
            <div class="od-info-row"><span class="od-info-k">类型</span><span class="od-info-v">{{ selectedConsumerApp.type === 1 ? 'API应用' : '数据应用' }}</span></div>
            <div class="od-info-row"><span class="od-info-k">网络</span><span class="od-info-v mono">{{ selectedConsumerApp.net_info?.vpc || '—' }}</span></div>
          </div>
        </div>

        <!-- 鉴权方式 -->
        <div class="od-section">
          <div class="od-label">鉴权方式</div>
          <div class="od-auth-badge" v-if="onboard.authMethod">
            <span class="auth-icon">{{ onboard.authMethod.icon }}</span>
            <div style="flex:1;">
              <div class="auth-name">{{ onboard.authMethod.name }}</div>
              <div class="mono text-secondary">{{ onboard.authMethod.type }}</div>
            </div>
            <span class="tag" :class="onboard.authMethod.strength === 'high' ? 'tag-ok' : 'tag-warn'">{{ onboard.authMethod.strengthLabel }}</span>
          </div>
        </div>

        <!-- 网络打通 -->
        <div class="od-section">
          <div class="od-label">网络打通</div>
          <label class="check">
            <input type="checkbox" v-model="onboard.network" />
            需要一并打通网络
          </label>
          <div class="od-hint" v-if="onboard.network">将自动创建网络打通工单，与鉴权凭证一并审批</div>
        </div>

        <!-- 申请理由 -->
        <div class="od-section">
          <div class="od-label">申请理由</div>
          <textarea v-model="onboard.reason" class="input textarea" placeholder="请说明接入用途..." rows="3"></textarea>
        </div>

        <div class="od-hint-box">
          <span class="od-hint-icon">💡</span>
          <div class="od-hint-text">
            申请通过后，凭证将在「应用管理 → 我接入了谁」中查看
          </div>
        </div>
      </div>

      <template #footer>
        <div class="drawer-footer">
          <button class="btn" @click="onboardOpen = false">取消</button>
          <button class="btn btn-primary" @click="submitOnboard" :disabled="!canSubmit || submitting">
            🚀 提交申请
          </button>
        </div>
      </template>
    </el-drawer>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { api } from '../api/client'
import { ElMessage } from 'element-plus'
import PageHeader from '../components/PageHeader.vue'
import EmptyState from '../components/EmptyState.vue'
import AuthMethodDrawer from '../components/AuthMethodDrawer.vue'

const apps = ref<any[]>([])
const details = ref<Record<number, any>>({})
const detail = ref<any>(null)
const me = ref<any>(null)
const meApps = ref<any[]>([])
const caps = ref<any[]>([])
const authDrawerOpen = ref(false)
const authMethod = ref<any>(null)

// 接入申请抽屉状态
const onboardOpen = ref(false)
const onboard = ref({
  consumer: 0,
  authMethod: null as any,
  network: true,
  reason: ''
})
const submitting = ref(false)

const NET_GROUPS: Record<string, string[]> = {
  基础设施: ['cloud', 'account', 'region'],
  网络: ['vpc', 'subnet', 'sg'],
  部署与探测: ['container', 'health'],
}
const netGroups = computed(() => {
  const info = detail.value?.net_info || {}
  const grouped: { title: string; rows: { k: string; v: any }[] }[] = []
  const used = new Set<string>()
  for (const [title, keys] of Object.entries(NET_GROUPS)) {
    const rows = keys.filter(k => k in info).map(k => ({ k, v: info[k] }))
    keys.forEach(k => used.add(k))
    if (rows.length) grouped.push({ title, rows })
  }
  const other = Object.keys(info).filter(k => !used.has(k)).map(k => ({ k, v: info[k] }))
  if (other.length) grouped.push({ title: '其他', rows: other })
  return grouped
})

const selectedConsumerApp = computed(() => {
  return meApps.value.find(a => a.id === onboard.value.consumer) || null
})

const canSubmit = computed(() => {
  return onboard.value.consumer && onboard.value.authMethod && onboard.value.reason.trim()
})

function capCount(id: number) { return caps.value.filter(c => c.app_id === id).length }
function appIcon(a: any) {
  const map: Record<string, string> = { cmdb: '🖥️', itsm: '📋', cloudportal: '☁️', monitor: '📈', 'ops-tool': '🛠️' }
  return map[a.code] || '📦'
}

async function openDetail(a: any) {
  let d = details.value[a.id]
  if (!d) {
    const r: any = await api.marketplaceAppDetail(a.id)
    d = r
    details.value[a.id] = d
  }
  detail.value = d
}

function openAuth(m: any) {
  authMethod.value = m
  authDrawerOpen.value = true
}

function openOnboardWithAuth(m: any) {
  onboard.value = {
    consumer: meApps.value[0]?.id || 0,
    authMethod: m,
    network: true,
    reason: ''
  }
  onboardOpen.value = true
}

async function submitOnboard() {
  if (!canSubmit.value) return
  submitting.value = true
  try {
    const r: any = await api.submitRequest({
      request_type: 3,
      consumer_app_id: onboard.value.consumer,
      provider_app_id: detail.value?.id,
      auth_method: onboard.value.authMethod.type,
      network_ticket: onboard.value.network,
      reason: onboard.value.reason || `接入申请：${detail.value?.name}`,
    })
    onboardOpen.value = false
    ElMessage.success(r.status === 'auto-approved' ? '接入申请已自动开通（凭证已签发）' : `接入申请已提交（#${r.id}），等待提供方审批`)
  } catch (e: any) {
    ElMessage.error(e.message)
  } finally {
    submitting.value = false
  }
}

onMounted(async () => {
  try {
    const [appsData, meData, capsData] = await Promise.all([api.marketplaceApps(), api.me(), api.marketplaceCapabilities()])
    apps.value = (appsData as any).items || appsData || []
    me.value = meData
    meApps.value = (meData as any).apps || []
    caps.value = (capsData as any).items || []
  } catch (e: any) { ElMessage.error(e.message) }
})
</script>

<style scoped>
.back-link { font-size: 13px; color: var(--text-secondary); background: none; border: none; cursor: pointer; display: block; margin-bottom: 8px; }
.section-title { font-size: 15px; font-weight: 700; margin: 22px 0 10px; }
.section-title .text-tertiary { font-size: 12px; font-weight: 400; }
.panel { background: var(--bg-card); border: 1px solid var(--border); border-radius: var(--radius); padding: 16px; margin-bottom: 14px; box-shadow: var(--shadow-sm); }
.app-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(220px, 1fr)); gap: 12px; }
.app-card { background: var(--bg-card); border: 1px solid var(--border); border-radius: var(--radius); padding: 16px; cursor: pointer; box-shadow: var(--shadow-sm); transition: all .15s; }
.app-card:hover { border-color: var(--brand); box-shadow: var(--shadow-md); transform: translateY(-2px); }
.app-icon { font-size: 24px; margin-bottom: 8px; }
.app-name { font-size: 15px; font-weight: 700; }
.app-meta { font-size: 12px; color: var(--text-secondary); }
.app-tags { margin-top: 10px; display: flex; gap: 6px; }
.net-group { margin-bottom: 14px; }
.net-group:last-child { margin-bottom: 0; }
.ng-title { font-size: 11px; font-weight: 700; color: var(--text-tertiary); text-transform: uppercase; letter-spacing: .05em; margin-bottom: 6px; }
.ng-rows { display: grid; grid-template-columns: 1fr 1fr; gap: 0 24px; }
.ng-row { display: flex; align-items: center; justify-content: space-between; padding: 7px 0; border-bottom: 1px dashed var(--border); font-size: 13px; }
.ng-k { color: var(--text-secondary); }
.ng-v { font-weight: 600; }

/* 鉴权卡片 */
.auth-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(320px, 1fr)); gap: 10px; }
.auth-item { border: 1px solid var(--border); padding: 12px 14px; border-radius: 8px; background: var(--bg-inset); display: flex; flex-direction: column; }
.auth-head { display: flex; align-items: center; gap: 10px; cursor: pointer; }
.auth-head:hover .auth-name { color: var(--brand); }
.auth-icon { font-size: 18px; }
.auth-name { font-size: 13px; font-weight: 700; transition: color .15s; }
.auth-desc { font-size: 12px; margin-top: 6px; flex: 1; }
.auth-actions { display: flex; align-items: center; justify-content: space-between; margin-top: 10px; padding-top: 8px; border-top: 1px dashed var(--border); }
.auth-more { font-size: 12px; color: var(--brand); font-weight: 500; cursor: pointer; }
.auth-more:hover { text-decoration: underline; }

/* 产品文档 */
.doc-panel { display: flex; flex-direction: column; gap: 6px; }
.doc-link { color: var(--brand); font-weight: 600; font-size: 14px; text-decoration: none; }
.doc-link:hover { text-decoration: underline; }
.doc-hint { font-size: 12px; color: var(--text-tertiary); }

/* 抽屉内表单 */
.onboard-drawer { display: flex; flex-direction: column; gap: 20px; }
.od-section { display: flex; flex-direction: column; gap: 8px; }
.od-label { font-size: 13px; font-weight: 700; color: var(--text); }
.od-target { display: flex; align-items: center; gap: 12px; padding: 12px; background: var(--bg-inset); border-radius: 10px; border: 1px solid var(--border); }
.od-icon { font-size: 28px; }
.od-name { font-size: 14px; font-weight: 700; }
.od-meta { font-size: 12px; color: var(--text-secondary); }
.od-consumer-info { margin-top: 8px; padding: 10px; background: var(--bg-inset); border-radius: 8px; font-size: 12px; }
.od-info-row { display: flex; justify-content: space-between; padding: 3px 0; }
.od-info-k { color: var(--text-secondary); }
.od-info-v { font-weight: 600; }
.od-auth-badge { display: flex; align-items: center; gap: 10px; padding: 12px; background: var(--brand-soft); border-radius: 10px; border: 2px solid var(--brand); }
.od-hint { font-size: 11px; color: var(--info); margin-top: 4px; }
.od-hint-box { display: flex; align-items: flex-start; gap: 8px; padding: 10px 12px; background: var(--brand-soft); border-radius: 8px; border: 1px solid var(--brand); }
.od-hint-icon { font-size: 14px; margin-top: 1px; }
.od-hint-text { font-size: 12px; color: var(--brand-strong); line-height: 1.5; }
.check { display: inline-flex; align-items: center; gap: 6px; font-size: 13px; cursor: pointer; }
.hint { font-size: 11px; color: var(--warning); }
.input { width: 100%; padding: 8px 12px; border: 1px solid var(--border); border-radius: 8px; background: var(--bg-card); color: var(--text); font-size: 13px; }
.textarea { resize: vertical; min-height: 80px; }
.drawer-footer { display: flex; justify-content: flex-end; gap: 10px; }

.btn { display: inline-flex; align-items: center; gap: 6px; height: 34px; padding: 0 14px; border-radius: 8px; font-size: 13px; font-weight: 600; border: 1px solid var(--border); background: var(--bg-card); color: var(--text); cursor: pointer; }
.btn:hover { background: var(--bg-hover); }
.btn-primary { background: var(--brand); color: #fff; border-color: var(--brand); }
.btn-primary:hover { background: var(--brand-strong); }
.btn-sm { height: 28px; padding: 0 10px; font-size: 12px; }
.btn:disabled { opacity: 0.5; cursor: not-allowed; }
.tag { font-family: var(--font-mono); font-size: 10px; font-weight: 600; padding: 2px 8px; border-radius: 999px; }
.tag-ok { background: var(--success-bg); color: var(--success); }
.tag-warn { background: var(--warning-bg); color: var(--warning); }
.tag-gray { background: var(--bg-inset); color: var(--text-tertiary); border: 1px solid var(--border); }
.mono { font-family: var(--font-mono); font-size: 12px; }
.text-secondary { color: var(--text-secondary); }
</style>
