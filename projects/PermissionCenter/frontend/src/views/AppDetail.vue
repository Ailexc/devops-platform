<template>
  <div class="app-detail" v-if="app">
    <PageHeader :title="`${appIcon} ${app.name}`" :desc="`${app.code} · ${app.type === 1 ? 'API' : '数据'} · 负责人 ${primaryOwner?.display_name || primaryOwner?.username || '—'} · v${appDetail?.app?.version || '—'}`">
      <template #actions>
        <button class="btn btn-ghost" @click="sync" :disabled="syncing">同步权限点</button>
        <router-link :to="`/apps/${$route.params.id}/routes`" class="btn btn-ghost">🧭 路由表（动作码登记）→</router-link>
        <router-link :to="`/capabilities?app=${app.code}`" class="btn btn-ghost">查看该应用的能力 →</router-link>
      </template>
    </PageHeader>

    <!-- 基础信息 -->
    <div class="section-title clickable" @click="toggleSection('basic')">
      <span class="chev">{{ collapsedSections.has('basic') ? '▸' : '▾' }}</span>
      📋 基础信息
    </div>
    <div v-show="!collapsedSections.has('basic')" class="panel basic-panel">
      <div class="basic-grid">
        <div class="basic-item">
          <div class="basic-k">应用描述</div>
          <div class="basic-v">{{ app.description || '—' }}</div>
        </div>
        <div class="basic-item">
          <div class="basic-k">开发语言</div>
          <div class="basic-v">{{ app.language || '—' }}</div>
        </div>
        <div class="basic-item">
          <div class="basic-k">OpenAPI</div>
          <div class="basic-v mono">{{ app.openapi_url || '—' }}</div>
        </div>
        <div class="basic-item">
          <div class="basic-k">产品文档</div>
          <div class="basic-v">
            <a v-if="app.doc_url" :href="app.doc_url" target="_blank" rel="noopener" class="doc-link">📖 {{ app.doc_url }}</a>
            <span v-else>—</span>
          </div>
        </div>
        <div class="basic-item">
          <div class="basic-k">所属组</div>
          <div class="basic-v">{{ ownerGroupText }}</div>
        </div>
        <div class="basic-item">
          <div class="basic-k">应用类型</div>
          <div class="basic-v">{{ app.type === 1 ? 'API 服务' : '数据服务' }}</div>
        </div>
        <div class="basic-item">
          <div class="basic-k">负责人</div>
          <div class="basic-v owner-list">
            <span v-for="o in appDetail?.owners || []" :key="o.user_id" class="owner-chip">
              {{ o.display_name || o.username }}<span class="mono" style="opacity:.6;margin-left:4px;">({{ o.username }})</span><span v-if="o.is_primary" class="owner-primary">主</span>
            </span>
            <span v-if="!appDetail?.owners?.length" class="text-tertiary">—</span>
          </div>
        </div>
      </div>
    </div>

    <!-- 权限点 -->
    <div class="section-title clickable" @click="toggleSection('permissions')">
      <span class="chev">{{ collapsedSections.has('permissions') ? '▸' : '▾' }}</span>
      <span>🔐 权限点</span>
      <span class="text-tertiary">OpenAPI 同步生成 · 共 {{ treeGroups.length }} 个分组 · {{ totalActions }} 个端点</span>
      <div class="section-actions" @click.stop>
        <button class="btn-link" @click="expandAll = !expandAll">{{ expandAll ? '全部折叠' : '全部展开' }}</button>
      </div>
    </div>
    <div v-show="!collapsedSections.has('permissions')" class="panel">
      <div v-for="g in treeGroups" :key="g.resource" class="tree-group">
        <div class="tree-title" @click="toggleGroup(g.resource)">
          <span class="chev">{{ openGroups.has(g.resource) ? '▾' : '▸' }}</span>
          {{ g.resource }}
          <span class="badge">{{ g.ops.length }} 个端点</span>
        </div>
        <div v-for="op in g.ops" :key="op.id" class="ep-wrap" v-show="openGroups.has(g.resource)" :class="{ open: openEp === op.id }">
          <div class="ep" @click="openEp = openEp === op.id ? 0 : op.id">
            <span class="method" :class="(op.method || '').toLowerCase()">{{ op.method }}</span>
            <span class="mono ep-path">{{ op.path }}</span>
            <span class="ep-code mono">{{ op.code }}</span>
            <span class="chev">{{ openEp === op.id ? '▾' : '▸' }}</span>
          </div>
          <div v-if="openEp === op.id" class="ep-body">
            <div class="eb-title">📝 接口描述</div><div class="eb-text">{{ op.name || op.description || '—' }}</div>
            <template v-if="op.req_example"><div class="eb-title">⬆️ 请求示例</div><pre class="eb-code">{{ op.req_example }}</pre></template>
            <template v-if="op.resp_example"><div class="eb-title">⬇️ 响应示例</div><pre class="eb-code">{{ op.resp_example }}</pre></template>
            <div v-if="!op.req_example && !op.resp_example" class="eb-empty">（暂无示例）</div>
          </div>
        </div>
      </div>
      <EmptyState v-if="!treeGroups.length" text="暂无接口（可点击「同步权限点」从 OpenAPI 生成）" />
    </div>

    <!-- 数据模型 -->
    <div class="section-title clickable" @click="toggleSection('models')">
      <span class="chev">{{ collapsedSections.has('models') ? '▸' : '▾' }}</span>
      🗂️ 数据模型 <span class="text-tertiary">OpenAPI schema · 点击展开字段</span>
    </div>
    <div v-show="!collapsedSections.has('models')" class="panel">
      <div v-for="m in models" :key="m.id" class="model-card" :class="{ open: openModel === m.id }">
        <div class="m-head" @click="openModel = openModel === m.id ? 0 : m.id">
          <span class="chev">{{ openModel === m.id ? '▾' : '▸' }}</span>
          <span class="mono m-code">{{ m.code }}</span>
          <span class="m-desc">{{ m.name }}</span>
          <span class="badge">{{ fieldCount(m) }} 字段</span>
        </div>
        <div v-if="openModel === m.id" class="m-body">
          <table class="data-table">
            <thead><tr><th>字段</th><th>类型</th><th>说明</th></tr></thead>
            <tbody>
              <tr v-for="(f, i) in fieldsOf(m)" :key="i">
                <td class="mono">{{ f.name }}</td>
                <td><span class="tag tag-gray">{{ f.type }}</span></td>
                <td class="text-secondary">{{ f.desc || '—' }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
      <EmptyState v-if="!models.length" text="暂无数据模型" />
    </div>

    <!-- 网络信息 -->
    <div class="section-title clickable" @click="toggleSection('network')">
      <span class="chev">{{ collapsedSections.has('network') ? '▸' : '▾' }}</span>
      🌐 网络信息
    </div>
    <div v-show="!collapsedSections.has('network')" class="panel">
      <div v-for="g in netGroups" :key="g.title" class="net-group">
        <div class="ng-title">{{ g.title }}</div>
        <div class="ng-rows">
          <div v-for="row in g.rows" :key="row.k" class="ng-row"><span class="ng-k">{{ row.k }}</span><span class="ng-v mono">{{ row.v }}</span></div>
        </div>
      </div>
    </div>

    <!-- 鉴权方式 -->
    <div class="section-title clickable" @click="toggleSection('auth')">
      <span class="chev">{{ collapsedSections.has('auth') ? '▸' : '▾' }}</span>
      🔐 鉴权方式 <span class="badge">{{ app.auth?.length || 0 }} 种</span> <span class="text-tertiary">点击查看运作机制与全流程</span>
    </div>
    <div v-show="!collapsedSections.has('auth')" class="panel auth-grid">
      <div v-for="m in app.auth || []" :key="m.type" class="auth-item" @click="openAuth(m)">
        <div class="auth-head"><span class="auth-icon">{{ m.icon }}</span><div style="flex:1;"><div class="auth-name">{{ m.name }}</div><div class="mono text-secondary">{{ m.type }}</div></div><span class="tag" :class="m.strength === 'high' ? 'tag-ok' : m.strength === 'medium' ? 'tag-warn' : ''">{{ m.strengthLabel }}</span></div>
        <div class="text-secondary auth-desc">{{ m.desc }}</div>
        <div class="auth-more">📖 查看运作机制 →</div>
      </div>
    </div>

    <!-- 接入与凭证 -->
    <div class="section-title clickable" @click="toggleSection('credentials')">
      <span class="chev">{{ collapsedSections.has('credentials') ? '▸' : '▾' }}</span>
      🔑 接入与凭证
    </div>
    <div v-show="!collapsedSections.has('credentials')">
      <div class="tabs">
        <button class="tab" :class="{ active: credentialTab === 'inbound' }" @click="credentialTab = 'inbound'">谁接入了我</button>
        <button class="tab" :class="{ active: credentialTab === 'outbound' }" @click="credentialTab = 'outbound'">我接入了谁</button>
      </div>
      <div class="panel">
        <div v-if="credentialTab === 'inbound'">
          <table v-if="inboundClients.length" class="data-table">
            <thead><tr><th>接入方</th><th>client_id</th><th>鉴权方式</th><th>状态</th></tr></thead>
            <tbody>
              <tr v-for="c in inboundClients" :key="c.client_id">
                <td>{{ appNameById(c.app_id) }}</td>
                <td class="mono">{{ c.client_id }}</td>
                <td class="mono">{{ c.auth_method || '—' }}</td>
                <td><span class="tag tag-ok">已签发</span></td>
              </tr>
            </tbody>
          </table>
          <EmptyState v-else text="暂无下游应用接入（对方在「应用市场」发起接入申请，审批通过后签发凭证）" />
        </div>
        <div v-else>
          <EmptyState v-if="!upstreams.length" text="本应用尚未申请外部应用能力" />
          <table v-else class="data-table">
            <thead><tr><th>目标应用</th><th>状态</th><th>client_id</th><th>操作</th></tr></thead>
            <tbody>
              <template v-for="(u, i) in upstreams" :key="i">
                <tr>
                  <td>
                    <div class="upstream-app">
                      <span class="mono">{{ u.upstream_code }}</span> {{ u.upstream_name }}
                    </div>
                  </td>
                  <td>
                    <span class="tag" :class="{
                      'tag-ok': u.credential_status === 'active',
                      'tag-amber': u.credential_status === 'pending',
                      'tag-gray': u.credential_status === 'rejected'
                    }">
                      {{ u.credential_status === 'active' ? '✅ 已通过' : u.credential_status === 'pending' ? '⏳ 申请中' : '❌ 已拒绝' }}
                    </span>
                  </td>
                  <td class="mono">{{ u.client_id || '—' }}</td>
                  <td>
                    <template v-if="u.credential_status === 'active'">
                      <el-dropdown trigger="click" @command="(cmd: string) => onUpstreamCmd(cmd, u, i)">
                        <button class="btn btn-sm">
                          ⚙️ 操作 <span class="chev">▾</span>
                        </button>
                        <template #dropdown>
                          <el-dropdown-menu class="upstream-menu">
                            <el-dropdown-item v-if="(u.interfaces || []).length" command="interfaces">
                              📡 接口契约
                            </el-dropdown-item>
                            <el-dropdown-item v-if="(u.models || []).length" command="models">
                              🗂️ 数据模型
                            </el-dropdown-item>
                            <el-dropdown-item v-if="u.doc_url" command="doc">
                              📖 产品文档
                            </el-dropdown-item>
                            <el-dropdown-item v-if="u.client_id" divided command="credential">
                              🔑 查看凭证
                            </el-dropdown-item>
                          </el-dropdown-menu>
                        </template>
                      </el-dropdown>
                    </template>
                    <span v-else-if="u.credential_status === 'pending'" class="text-tertiary">等待审批</span>
                    <button v-else-if="u.credential_status === 'rejected'" class="btn btn-sm btn-outline">重新申请</button>
                  </td>
                </tr>
                <tr v-if="openUpstreamPanel?.idx === i && openUpstreamPanel?.kind === 'interfaces'" class="upstream-ep-row">
                  <td colspan="4">
                    <div v-if="(u.interfaces || []).length" class="ep-list">
                      <div v-for="op in u.interfaces" :key="op.action" class="ep-item">
                        <span class="method" :class="(op.method || '').toLowerCase()">{{ op.method }}</span>
                        <span class="mono ep-path">{{ op.path }}</span>
                        <span class="text-secondary ep-name">{{ op.name || op.action }}</span>
                        <div v-if="op.req_example || op.resp_example" class="ep-ex">
                          <div v-if="op.req_example" class="ex"><span class="ex-t">⬆️ 请求</span><pre class="ex-c">{{ op.req_example }}</pre></div>
                          <div v-if="op.resp_example" class="ex"><span class="ex-t">⬇️ 响应</span><pre class="ex-c">{{ op.resp_example }}</pre></div>
                        </div>
                      </div>
                    </div>
                    <div v-else class="text-tertiary" style="font-size:12px;">暂无接口契约</div>
                  </td>
                </tr>
                <tr v-if="openUpstreamPanel?.idx === i && openUpstreamPanel?.kind === 'models'" class="upstream-ep-row">
                  <td colspan="4">
                    <div class="umodels">
                      <div v-for="m in u.models || []" :key="m.code" class="umodel">
                        <div class="um-head">
                          <span class="mono um-code">{{ m.code }}</span>
                          <span class="um-name">{{ m.name }}</span>
                          <span class="badge">{{ fieldsOf(m).length }} 字段</span>
                        </div>
                        <table class="data-table um-table">
                          <thead><tr><th>字段</th><th>类型</th><th>说明</th></tr></thead>
                          <tbody>
                            <tr v-for="(f, fi) in fieldsOf(m)" :key="fi">
                              <td class="mono">{{ f.name }}</td>
                              <td><span class="tag tag-gray">{{ f.type }}</span></td>
                              <td class="text-secondary">{{ f.desc || '—' }}</td>
                            </tr>
                          </tbody>
                        </table>
                      </div>
                    </div>
                    <div v-if="!(u.models || []).length" class="text-tertiary" style="font-size:12px;">暂无数据模型</div>
                  </td>
                </tr>
              </template>
            </tbody>
          </table>
        </div>
      </div>
    </div>

    

    <AuthMethodDrawer v-model="authDrawerOpen" :method="authMethod" />

    <!-- 凭证查看弹窗 -->
    <el-dialog v-model="credentialDialogVisible" title="🔑 您的凭证" width="480">
      <div class="credential-dialog" v-if="currentCredential">
        <div class="cred-field">
          <label>client_id</label>
          <div class="cred-value">
            <span class="mono">{{ currentCredential.client_id }}</span>
            <button class="btn btn-sm" @click="copyToClipboard(currentCredential.client_id)">复制</button>
          </div>
        </div>
        <div class="cred-field">
          <label>client_secret</label>
          <div class="cred-value">
            <template v-if="secretRevealed">
              <span class="mono">{{ currentCredential.secret }}</span>
              <button class="btn btn-sm" @click="copyToClipboard(currentCredential.secret)">复制</button>
            </template>
            <template v-else>
              <span class="mono">••••••••••••••••</span>
              <button class="btn btn-sm btn-primary" @click="rotateSecret">轮换并复制</button>
            </template>
          </div>
        </div>
        <div class="cred-warning" v-if="!secretRevealed">
          ⚠️ 将生成新的 Secret，旧的 Secret 将立即失效
        </div>
        <div class="cred-success" v-else>
          ✅ 请立即复制保存，关闭弹窗后将无法再次查看
        </div>
      </div>
    </el-dialog>
  </div>
  <div v-else class="empty-state" style="padding:60px;">加载中…</div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import { api } from '../api/client'
import { ElMessage } from 'element-plus'
import PageHeader from '../components/PageHeader.vue'
import EmptyState from '../components/EmptyState.vue'
import AuthMethodDrawer from '../components/AuthMethodDrawer.vue'

const route = useRoute()
const appId = Number(route.params.id)
const app = ref<any>(null)
const appDetail = ref<any>(null)
const actions = ref<any[]>([])
const models = ref<any[]>([])
const allClients = ref<any[]>([])
const accessors = ref<any[]>([])
const upstreams = ref<any[]>([])
const ledgerTab = ref<'accessors' | 'upstreams'>('accessors')
const credentialTab = ref<'inbound' | 'outbound'>('inbound')
const credentialDialogVisible = ref(false)
const currentCredential = ref<any>(null)
const secretRevealed = ref(false)
const openUpstreamPanel = ref<{ idx: number; kind: 'interfaces' | 'models' } | null>(null) // 我接入了谁 展开面板
const openEp = ref(0)
const openGroups = ref(new Set<string>())
const expandAll = ref(false)
const openModel = ref(0)
const collapsedSections = ref(new Set<string>())
const totalActions = computed(() => treeGroups.value.reduce((sum, g) => sum + g.ops.length, 0))

const syncing = ref(false)
const authDrawerOpen = ref(false)
const authMethod = ref<any>(null)

const NET_GROUPS: Record<string, string[]> = {
  基础设施: ['cloud', 'account', 'region'],
  网络: ['vpc', 'subnet', 'sg'],
  部署与探测: ['container', 'health'],
}
const netGroups = computed(() => {
  const info = app.value?.net_info || {}
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

const appIcon = computed(() => {
  const map: Record<string, string> = { cmdb: '🖥️', itsm: '📋', cloudportal: '☁️', monitor: '📈', 'ops-tool': '🛠️' }
  return map[app.value?.code] || '📦'
})
const primaryOwner = computed(() => {
  const owners = appDetail.value?.owners || []
  return owners.find((o: any) => o.is_primary) || owners[0] || null
})
const ownerGroupText = computed(() => {
  const og = appDetail.value?.owner_group
  if (!og) return '—'
  const pn = og.path_names || [og.name]
  return pn.join(' → ')
})
const treeGroups = computed(() => {
  const m = new Map<string, any[]>()
  for (const a of actions.value) {
    if (!m.has(a.resource)) m.set(a.resource, [])
    m.get(a.resource)!.push(a)
  }
  return [...m.entries()].map(([resource, ops]) => ({ resource, ops }))
})

const inboundClients = computed(() => allClients.value.filter((c: any) => c.app_id === appId))
function appNameById(id: number) { return appsList.value.find((a: any) => a.id === id)?.name || `#${id}` }
const appsList = ref<any[]>([])

function fieldsOf(m: any) {
  try {
    const raw = m.fields || m.attributes_schema
    if (!raw) return []
    if (typeof raw === 'string') return JSON.parse(raw)
    if (Array.isArray(raw)) return raw
    return Object.entries(raw).map(([name, type]) => ({ name, type: String(type) }))
  } catch { return [] }
}
function fieldCount(m: any) { return fieldsOf(m).length }

function subjectTypeLabel(t: number) { return { 1: '用户', 2: '组', 3: '组织', 4: '应用' }[t] || t }
function sourceLabel(s: number) { return { 1: '直接授权', 2: '申请审批', 3: '应用间' }[s] || s }

watch(expandAll, (v) => {
  if (v) {
    treeGroups.value.forEach(g => openGroups.value.add(g.resource))
  } else {
    openGroups.value.clear()
  }
})

function toggleGroup(resource: string) {
  if (openGroups.value.has(resource)) {
    openGroups.value.delete(resource)
  } else {
    openGroups.value.add(resource)
  }
}

function toggleSection(key: string) {
  if (collapsedSections.value.has(key)) {
    collapsedSections.value.delete(key)
  } else {
    collapsedSections.value.add(key)
  }
}

async function sync() {
  syncing.value = true
  try {
    const res = await api.syncApp(appId)
    ElMessage.success(`同步完成：${(res as any).actions} 个权限点`)
    loadActions()
  } catch (e: any) {
    ElMessage.error(e.message)
  } finally {
    syncing.value = false
  }
}

async function loadActions() {
  const data = await api.actions(appId)
  actions.value = (data as any).items || data || []
}

function openAuth(m: any) {
  authMethod.value = m
  authDrawerOpen.value = true
}

function viewCredential(item: any) {
  currentCredential.value = item
  secretRevealed.value = false
  credentialDialogVisible.value = true
}

// 我接入了谁 操作列下拉：接口契约/数据模型（展开面板）| 产品文档/查看凭证（动作）
function onUpstreamCmd(cmd: string, u: any, idx: number) {
  if (cmd === 'interfaces' || cmd === 'models') {
    openUpstreamPanel.value =
      openUpstreamPanel.value?.idx === idx && openUpstreamPanel.value?.kind === cmd
        ? null
        : { idx, kind: cmd }
  } else if (cmd === 'doc') {
    if (u.doc_url) window.open(u.doc_url, '_blank', 'noopener')
  } else if (cmd === 'credential') {
    viewCredential(u)
  }
}

async function rotateSecret() {
  if (!currentCredential.value) return
  try {
    const res = await api.rotateClientSecret(currentCredential.value.client_id)
    currentCredential.value.secret = (res as any).client_secret
    secretRevealed.value = true
  } catch (e: any) {
    ElMessage.error(e.message)
  }
}

function copyToClipboard(text: string) {
  navigator.clipboard.writeText(text)
  ElMessage.success('已复制到剪贴板')
}

onMounted(async () => {
  try {
    const [appData, detailData, actionsData, clientsData, accessorsData, upstreamsData, appsData, modelsData] = await Promise.all([
      api.appDetail(appId),
      api.appDetail(appId),
      api.actions(appId),
      api.clients(),
      api.accessors(appId),
      api.upstreams(appId),
      api.apps(),
      api.resourceModels()
    ])
    app.value = (appData as any).app
    appDetail.value = detailData
    actions.value = (actionsData as any).items || actionsData || []
    allClients.value = (clientsData as any).items || clientsData || []
    accessors.value = (accessorsData as any).items || accessorsData || []
    upstreams.value = (upstreamsData as any).items || upstreamsData || []
    appsList.value = (appsData as any).items || appsData || []
    // 数据模型按应用归属展示（resource_models 全局投影含各应用资源，AppID=0 旧数据视为全局）
    const allModels = (modelsData as any).items || modelsData || []
    models.value = allModels.filter((m: any) => !m.app_id || m.app_id === appId)
  } catch (e: any) {
    ElMessage.error(e.message)
  }
})
</script>

<style scoped>
.section-title { font-size: 15px; font-weight: 700; margin: 22px 0 10px; display: flex; align-items: center; gap: 10px; flex-wrap: wrap; }
.section-title.clickable { cursor: pointer; user-select: none; padding: 8px 12px; border-radius: 8px; transition: background .15s; margin-left: -12px; }
.section-title.clickable:hover { background: var(--bg-inset); }
.section-title .chev { font-size: 12px; color: var(--text-tertiary); }
.section-title .text-tertiary { font-size: 12px; font-weight: 400; color: var(--text-tertiary); }
.section-actions { margin-left: auto; }
.btn-link { font-size: 12px; color: var(--brand); background: none; border: none; cursor: pointer; font-weight: 600; padding: 4px 8px; border-radius: 4px; }
.btn-link:hover { background: var(--brand-soft); }
.panel { background: var(--bg-card); border: 1px solid var(--border); border-radius: var(--radius); padding: 16px; margin-bottom: 14px; box-shadow: var(--shadow-sm); }

/* 基础信息 */
.basic-panel { padding: 20px; }
.basic-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)); gap: 18px 32px; }
.basic-item { display: flex; flex-direction: column; gap: 4px; }
.basic-k { font-size: 11px; font-weight: 700; color: var(--text-tertiary); text-transform: uppercase; letter-spacing: .05em; }
.basic-v { font-size: 14px; color: var(--text); word-break: break-all; }
.owner-list { display: flex; flex-wrap: wrap; gap: 6px; }
.owner-chip { display: inline-flex; align-items: center; padding: 3px 10px; background: var(--bg-inset); border: 1px solid var(--border); border-radius: 999px; font-size: 12px; }
.owner-primary { margin-left: 4px; padding: 0 5px; font-size: 10px; font-weight: 700; background: var(--brand); color: #fff; border-radius: 4px; }
.doc-link { color: var(--brand); text-decoration: none; font-size: 13px; word-break: break-all; }
.doc-link:hover { text-decoration: underline; }

/* 接口契约（我接入了谁） */
.upstream-ep-row td { background: var(--bg-secondary); }
.upstream-menu { min-width: 150px; }
.upstream-menu .el-dropdown-menu__item { font-size: 13px; }
.umodels { display: flex; flex-direction: column; gap: 10px; }
.umodel { border: 1px solid var(--border); border-radius: 8px; background: var(--bg-card); overflow: hidden; }
.um-head { display: flex; align-items: center; gap: 10px; padding: 8px 12px; font-size: 13px; }
.um-code { font-weight: 700; }
.um-name { color: var(--text-secondary); font-size: 12px; flex: 1; }
.um-table { border-top: 1px solid var(--border); }
.um-table th { background: var(--bg-inset); }
.ep-list { display: flex; flex-direction: column; gap: 8px; }
.ep-item { border: 1px solid var(--border); border-radius: 6px; padding: 8px 10px; background: var(--bg-card); display: flex; flex-wrap: wrap; align-items: center; gap: 8px; }
.ep-name { font-size: 12px; flex: 1; min-width: 80px; }
.ep-ex { width: 100%; display: flex; gap: 12px; flex-wrap: wrap; }
.ex { flex: 1; min-width: 220px; display: flex; flex-direction: column; gap: 3px; }
.ex-t { font-size: 11px; font-weight: 600; color: var(--text-tertiary); }
.ex-c { font-family: var(--font-mono); font-size: 11px; background: var(--bg-secondary); border: 1px solid var(--border); border-radius: 4px; padding: 6px 8px; white-space: pre-wrap; word-break: break-all; margin: 0; }
.method { font-family: var(--font-mono); font-size: 10px; font-weight: 700; padding: 2px 6px; border-radius: 4px; }
.method.get { background: var(--info-bg, #cffafe); color: var(--info, #0891b2); }
.method.post { background: var(--success-bg, #dcfce7); color: var(--success, #16a34a); }
.method.put, .method.patch { background: var(--warning-bg, #fef3c7); color: var(--warning, #d97706); }
.method.delete { background: rgba(239,68,68,.12); color: #dc2626; }
.ep-path { color: var(--text); font-size: 12px; }

.tree-group { margin-bottom: 12px; }
.tree-title { font-size: 13px; font-weight: 700; padding: 10px 12px; display: flex; align-items: center; gap: 8px; cursor: pointer; user-select: none; background: var(--bg-inset); border-radius: 8px; border: 1px solid var(--border); transition: all .15s; }
.tree-title:hover { background: var(--brand-soft); border-color: var(--brand); color: var(--brand); }
.ep-wrap { border: 1px solid var(--border); border-radius: 8px; margin-bottom: 6px; overflow: hidden; transition: all .15s; }
.ep-wrap:hover { border-color: var(--brand); }
.ep { display: flex; align-items: center; gap: 10px; padding: 10px 12px; cursor: pointer; font-size: 13px; }
.ep:hover { background: var(--brand-soft); }
.method { font-family: var(--font-mono); font-size: 10px; font-weight: 700; padding: 2px 6px; border-radius: 4px; }
.method.get { background: var(--info-bg); color: var(--info); }
.method.post { background: var(--success-bg); color: var(--success); }
.method.put { background: var(--warning-bg); color: var(--warning); }
.method.delete { background: var(--danger-bg); color: var(--danger); }
.ep-path { color: var(--text-secondary); }
.ep-code { margin-left: auto; color: var(--text-tertiary); font-size: 11px; }
.chev { color: var(--text-tertiary); font-size: 11px; }
.ep-body { padding: 10px 12px; border-top: 1px solid var(--border); background: var(--bg-inset); }
.eb-title { font-size: 11px; font-weight: 700; color: var(--text-secondary); margin: 6px 0 4px; }
.eb-text { font-size: 12px; color: var(--text-secondary); }
.eb-code { background: var(--bg-card); border: 1px solid var(--border); border-radius: 6px; padding: 8px; font-family: var(--font-mono); font-size: 11px; white-space: pre-wrap; }
.eb-empty { font-size: 11px; color: var(--text-tertiary); }
.model-card { border: 1px solid var(--border); border-radius: 8px; margin-bottom: 8px; overflow: hidden; }
.m-head { display: flex; align-items: center; gap: 10px; padding: 10px 12px; cursor: pointer; font-size: 13px; }
.m-head:hover { background: var(--bg-hover); }
.m-code { font-weight: 700; }
.m-desc { color: var(--text-secondary); font-size: 12px; }
.m-body { border-top: 1px solid var(--border); background: var(--bg-inset); }
.net-group { margin-bottom: 14px; }
.net-group:last-child { margin-bottom: 0; }
.ng-title { font-size: 11px; font-weight: 700; color: var(--text-tertiary); text-transform: uppercase; letter-spacing: .05em; margin-bottom: 6px; }
.ng-rows { display: grid; grid-template-columns: 1fr 1fr; gap: 0 24px; }
.ng-row { display: flex; align-items: center; justify-content: space-between; padding: 7px 0; border-bottom: 1px dashed var(--border); font-size: 13px; }
.ng-k { color: var(--text-secondary); }
.ng-v { font-weight: 600; }
.auth-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(300px, 1fr)); gap: 10px; }
.auth-item { border: 1px solid var(--border); border-radius: 8px; padding: 12px 14px; background: var(--bg-inset); }
.auth-head { display: flex; align-items: center; gap: 10px; }
.auth-icon { font-size: 18px; }
.auth-name { font-size: 13px; font-weight: 700; }
.auth-desc { font-size: 12px; margin-top: 6px; }
.auth-item { cursor: pointer; transition: border-color .15s, box-shadow .15s; }
.auth-item:hover { border-color: var(--brand); box-shadow: var(--shadow-sm); }
.auth-more { margin-top: 8px; font-size: 12px; color: var(--brand); font-weight: 500; }
.tabs { display: flex; gap: 0; border: 1px solid var(--border); border-radius: 8px; width: fit-content; overflow: hidden; margin-bottom: 12px; }
.tab { padding: 8px 20px; font-size: 13px; font-weight: 500; background: var(--bg-card); border: none; border-right: 1px solid var(--border); color: var(--text-secondary); cursor: pointer; }
.tab:last-child { border-right: none; }
.tab.active { background: var(--brand-soft); color: var(--brand-strong); font-weight: 600; }
.data-table { width: 100%; border-collapse: collapse; font-size: 13px; }
.data-table th { text-align: left; padding: 8px 12px; font-family: var(--font-mono); font-size: 10px; text-transform: uppercase; color: var(--text-secondary); background: var(--bg-secondary); border-bottom: 1px solid var(--border); }
.data-table td { padding: 8px 12px; border-bottom: 1px solid var(--border); }
.badge { display: inline-flex; align-items: center; padding: 3px 10px; border-radius: 999px; font-size: 11px; font-weight: 600; background: var(--brand-soft); color: var(--brand-strong); }
.tag { font-family: var(--font-mono); font-size: 10px; font-weight: 600; padding: 2px 8px; border-radius: 999px; }
.tag-ok { background: var(--success-bg); color: var(--success); }
.tag-warn { background: var(--warning-bg); color: var(--warning); }
.tag-gray { background: var(--bg-inset); color: var(--text-tertiary); border: 1px solid var(--border); }
.btn { display: inline-flex; align-items: center; gap: 6px; height: 34px; padding: 0 14px; border-radius: 8px; font-size: 13px; font-weight: 600; border: 1px solid var(--border); background: var(--bg-card); color: var(--text); cursor: pointer; text-decoration: none; }
.btn:hover { background: var(--bg-hover); }
.btn-ghost { background: transparent; color: var(--text-secondary); }
.mono { font-family: var(--font-mono); font-size: 12px; }
.text-secondary { color: var(--text-secondary); }
.text-tertiary { color: var(--text-tertiary); }
.empty-state { padding: 40px; text-align: center; color: var(--text-tertiary); font-size: 13px; }
.upstream-app { display: flex; align-items: center; gap: 8px; }
.credential-dialog { display: flex; flex-direction: column; gap: 16px; }
.cred-field { display: flex; flex-direction: column; gap: 6px; }
.cred-field label { font-size: 12px; font-weight: 600; color: var(--text-secondary); text-transform: uppercase; }
.cred-value { display: flex; align-items: center; gap: 8px; padding: 10px 12px; background: var(--bg-inset); border: 1px solid var(--border); border-radius: 8px; }
.cred-value .mono { flex: 1; font-size: 13px; }
.cred-warning { font-size: 12px; color: var(--warning); padding: 10px; background: var(--warning-bg); border-radius: 8px; }
.cred-success { font-size: 12px; color: var(--success); padding: 10px; background: var(--success-bg); border-radius: 8px; }
</style>