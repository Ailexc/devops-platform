<template>
  <div class="rt-page">
    <PageHeader
      :title="`🧭 路由表 · ${app?.name || ''}`"
      desc="动作码三段式登记（应用:资源:动作）· 运行期纯查表零推断 · 归档不删可查不可用"
    >
      <template #actions>
        <span class="tag tag-blue">路由表 v{{ version }}</span>
        <span class="tag tag-gray">{{ items.length }} 条路由</span>
        <button class="btn btn-ghost" @click="load">⟳ 刷新</button>
        <button class="btn" @click="runOnboard">🩺 接入体检</button>
        <button class="btn btn-primary" @click="showImport = true">📥 导入路由</button>
      </template>
    </PageHeader>

    <!-- 接入体检报告（§3.9 五类硬校验回执）：阻断=不修完不能接入；待确认=停在未完成态 -->
    <div v-if="onboard" class="section-title">
      🩺 接入体检报告
      <span class="tag" :class="statusTag(onboard.status)">{{ statusText(onboard.status) }}</span>
      <span class="section-hint">{{ onboard.actions }} 条路由 · 动作码已登记 {{ onboard.registered }} 条</span>
      <span class="section-hint">导入/注册时自动跑，此为最新回执</span>
    </div>
    <div v-if="onboard" class="panel ob-panel">
      <div v-if="!onboard.blocked.length && !onboard.warnings.length" class="ob-ok">
        ✅ 五类硬校验全绿（缺动作/格式/重复/配置自洽/导入一致性）
      </div>
      <div v-for="(b, i) in onboard.blocked" :key="'ob' + i" class="ob-block">
        <span class="tag tag-red">{{ b.code }}</span>
        <span class="mono">{{ b.method }} {{ b.path }}</span>
        <span v-if="b.action" class="mono ob-action">{{ b.action }}</span>
        <span class="ob-reason">{{ b.reason }}</span>
      </div>
      <div v-for="(w, i) in onboard.warnings" :key="'ow' + i" class="ob-warn">
        <span class="tag tag-amber">{{ w.code }}</span>
        <span class="mono">{{ w.method }} {{ w.path }}</span>
        <span class="mono ob-action">{{ w.action }}</span>
        <span class="ob-reason">{{ w.reason }}</span>
      </div>
    </div>

    <!-- 待确认队列：推断预填永不直接生效，人工确认后落表 -->
    <div class="section-title">
      ⚠️ 待确认队列
      <span class="tag" :class="pending.length ? 'tag-amber' : 'tag-gray'">{{ pending.length }}</span>
      <span class="section-hint">推断只在导入、预填不生效——确认后才进路由表</span>
    </div>
    <div v-if="pending.length" class="panel">
      <table class="rt-table">
        <thead>
          <tr><th>方法</th><th>路径</th><th>推断动作码</th><th>推断依据</th><th style="width:300px">操作</th></tr>
        </thead>
        <tbody>
          <tr v-for="p in pending" :key="p.id">
            <td class="mono">{{ p.method }}</td>
            <td class="mono">{{ p.path }}</td>
            <td class="mono">{{ p.inferred_code || '— 推不出 —' }}</td>
            <td class="hint">{{ p.reason }}</td>
            <td>
              <input v-if="p._edit" v-model="p._code" class="input input-inline" placeholder="app:resource:verb" />
              <button class="btn btn-sm btn-primary" @click="confirmPending(p)">
                {{ p._edit ? '✓ 落表' : '✓ 确认' }}
              </button>
              <button v-if="!p._edit" class="btn btn-sm" @click="p._edit = true; p._code = p.inferred_code">✏️ 改码</button>
              <button class="btn btn-sm btn-ghost" @click="discardPending(p)">✕ 丢弃</button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- 路由表 -->
    <div class="section-title">📋 路由表 <span class="section-hint">五格 = 动作 / 读写 / 数据级取材声明 / 范围参数 / 资源</span></div>
    <div class="panel rt-wrap">
      <table class="rt-table">
        <thead>
          <tr>
            <th>方法</th><th>路径</th><th>动作码</th><th>读写</th><th>档位</th>
            <th>取材声明</th><th>范围参数</th><th>状态</th><th style="width:200px">操作</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="a in items" :key="a.id" :class="{ archived: a.status === 'archived' }">
            <td class="mono">{{ a.method || '—' }}</td>
            <td class="mono">{{ a.path || '—' }}</td>
            <td class="mono code">{{ a.code }}</td>
            <td>
              <span class="tag" :class="rwOf(a) === 'read' ? 'tag-blue' : 'tag-amber'">{{ rwOf(a) }}</span>
            </td>
            <td>
              <span class="tag" :class="a.need_data ? 'tag-ok' : 'tag-gray'">{{ a.need_data ? '数据级' : '接口级' }}</span>
            </td>
            <td class="mono hint">{{ materialBrief(a) }}</td>
            <td class="mono hint">{{ scopeBrief(a) }}</td>
            <td>
              <span class="tag" :class="a.status === 'archived' ? 'tag-gray' : 'tag-ok'">
                {{ a.status === 'archived' ? '归档' : 'active' }}
              </span>
            </td>
            <td>
              <button class="btn btn-sm" @click="openEdit(a)">✏️ 登记</button>
              <button class="btn btn-sm" @click="openMigrate(a)">🔀 迁移</button>
              <button v-if="a.status === 'archived'" class="btn btn-sm" @click="restore(a)">↩️ 恢复</button>
              <button v-else class="btn btn-sm btn-ghost" @click="archive(a)">📦 归档</button>
            </td>
          </tr>
        </tbody>
      </table>
      <div v-if="!items.length" class="empty">暂无路由——点右上「导入路由」拉取 OpenAPI 或粘贴字典</div>
    </div>

    <!-- 导入弹窗 -->
    <div v-if="showImport" class="modal-mask" @click.self="showImport = false">
      <div class="modal-box modal-wide">
        <div class="modal-title">导入路由（§3.8 三种建法）</div>
        <label>来源
          <select v-model="imp.source" class="input">
            <option value="openapi">OpenAPI（x-action 源头标注 = 100% 档，缺标注自动推断入队）</option>
            <option value="dict">字典粘贴（显式登记 / 缺省推断入待确认队列）</option>
          </select>
        </label>
        <template v-if="imp.source === 'dict'">
          <label>字典条目（每行：<span class="mono">METHOD /path [app:resource:verb]</span>，动作码可省→推断入队）
            <textarea v-model="imp.text" class="input mono" rows="8" placeholder="POST /api/v1/instances/reboot&#10;POST /api/v1/disks&#10;GET /api/v1/disks&#10;PATCH /api/v1/disks/{id} cmdb:disk:edit"></textarea>
          </label>
        </template>
        <div v-else class="notice-inline">
          拉取应用 OpenAPI 文档 → 解析 x-action 标注（100% 档）→ 无标注的按推断四条+一兜底进待确认队列。
        </div>
        <div v-if="impReport" class="report">
          <div class="report-line">
            <span class="tag tag-ok">落表 {{ impReport.imported }}</span>
            <span class="tag" :class="impReport.pending_count ? 'tag-amber' : 'tag-gray'">入队 {{ impReport.pending_count || 0 }}</span>
            <span class="tag" :class="impReport.blocked?.length ? 'tag-red' : 'tag-gray'">拦截 {{ impReport.blocked?.length || 0 }}</span>
            <span class="tag tag-blue">v{{ impReport.version }}</span>
          </div>
          <div v-for="(b, i) in impReport.blocked || []" :key="i" class="report-block">
            <span class="mono">{{ b.method }} {{ b.path }}</span> — {{ b.reason }}
          </div>
        </div>
        <div class="modal-foot">
          <button class="btn btn-ghost" @click="showImport = false; impReport = null">关闭</button>
          <button class="btn btn-primary" @click="doImport" :disabled="importing">
            {{ importing ? '导入中…' : '开始导入' }}
          </button>
        </div>
        <div v-if="impErr" class="modal-err">{{ impErr }}</div>
      </div>
    </div>

    <!-- 五格登记弹窗 -->
    <div v-if="showEdit" class="modal-mask" @click.self="showEdit = false">
      <div class="modal-box modal-wide">
        <div class="modal-title">登记接口（五格）</div>
        <div class="grid2">
          <label>接口（自动带出）
            <input class="input mono" :value="`${edit.method} ${edit.path}`" readonly />
          </label>
          <label>动作码（改码走迁移，此处只读）
            <input class="input mono" :value="edit.code" readonly />
          </label>
        </div>
        <label>读/写（唯一的分类——UI 分组/只读聚合/审计分级用）
          <div class="radio-row">
            <label class="radio"><input type="radio" value="read" v-model="edit.rw" /> 读</label>
            <label class="radio"><input type="radio" value="write" v-model="edit.rw" /> 写</label>
          </div>
        </label>
        <label class="check-row">
          <input type="checkbox" v-model="edit.need_data" />
          数据级（需要行属性判定——勾选后【取材声明】★必填）
        </label>
        <template v-if="edit.need_data">
          <label>取材声明（三选一，按序命中即停）
            <select v-model="edit.mode" class="input">
              <option value="id_path">① 目标行存在 → id 取值路径（按 id 点查权威行）</option>
              <option value="envelope">② 创建类 → 信封字段路径（请求即"未来的行"）</option>
              <option value="fetch_source">③ 补救 → 自定义回源（历史接口兜底）</option>
            </select>
          </label>
          <label v-if="edit.mode === 'id_path'">id 取值路径
            <input v-model="edit.idPath" class="input mono" placeholder="path.id / body.instance_id / body.ids[*]" />
          </label>
          <template v-if="edit.mode === 'envelope'">
            <label>信封字段路径（默认 .meta.account）
              <input v-model="edit.fieldPath" class="input mono" placeholder=".meta.account" />
            </label>
            <div class="notice-inline">meta 板块放鉴权字段是组内规范；变更类判定仍按 id 查权威行，不信自报。</div>
          </template>
          <template v-if="edit.mode === 'fetch_source'">
            <div class="grid2">
              <label>回源 url
                <input v-model="edit.url" class="input mono" placeholder="GET /api/v1/disks/{disk_id}" />
              </label>
              <label>pick（验条件字段）
                <input v-model="edit.pick" class="input mono" placeholder="account" />
              </label>
            </div>
            <label>绑定字典 bind（JSON：每个占位符必须有绑定，from ∈ path/query/body/const/ctx）
              <textarea v-model="edit.bindJson" class="input mono" rows="4" spellcheck="false"></textarea>
            </label>
          </template>
        </template>
        <label>范围参数（仅 list 动作——判定两步的契约登记位）
          <div class="grid2">
            <input v-model="edit.param" class="input mono" placeholder="参数名，如 account" />
            <select v-model="edit.location" class="input">
              <option value="query">query（规范）</option>
              <option value="header">header（历史兼容通道）</option>
            </select>
          </div>
        </label>
        <div class="modal-foot">
          <button class="btn btn-ghost" @click="showEdit = false">取消</button>
          <button class="btn btn-primary" @click="saveEdit" :disabled="saving">{{ saving ? '保存中…' : '保存' }}</button>
        </div>
        <div v-if="editErr" class="modal-err">{{ editErr }}</div>
      </div>
    </div>

    <!-- 迁移弹窗（变更阻断 → 一键迁移） -->
    <div v-if="showMig" class="modal-mask" @click.self="showMig = false">
      <div class="modal-box modal-wide">
        <div class="modal-title">🔀 动作码迁移（改名不存在——语义等价才迁移）</div>
        <label>当前
          <input class="input mono" :value="mig.code" readonly />
        </label>
        <label>新动作码
          <input v-model="mig.newCode" class="input mono" placeholder="app:resource:verb（全小写三段）" />
        </label>
        <div v-if="mig.affected" class="affected">
          <div class="affected-title">⚠️ 变更阻断：以下引用方受影响（确认语义等价后继续）</div>
          <div v-for="p in mig.affected.policies || []" :key="'p' + p.id" class="affected-item">
            📜 策略 #{{ p.id }} {{ p.name }}
          </div>
          <div v-for="cp in mig.affected.capabilities || []" :key="'c' + cp.id" class="affected-item">
            📦 能力包 #{{ cp.id }} {{ cp.name }}
          </div>
          <label class="check-row"><input type="checkbox" v-model="mig.confirmed" /> 我确认语义等价（仅换词），执行一键迁移</label>
        </div>
        <div class="modal-foot">
          <button class="btn btn-ghost" @click="showMig = false">取消</button>
          <button class="btn btn-primary" @click="doMigrate" :disabled="migBusy || (mig.affected && !mig.confirmed)">
            {{ migBusy ? '迁移中…' : mig.affected ? '确认迁移' : '迁移' }}
          </button>
        </div>
        <div v-if="migErr" class="modal-err">{{ migErr }}</div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { useRoute } from 'vue-router'
import { api, requestWithStatus } from '../api/client'
import PageHeader from '../components/PageHeader.vue'

const route = useRoute()
const appId = computed(() => Number(route.params.id))

const app = ref<any>(null)
const onboard = ref<any>(null)
const items = ref<any[]>([])
const pending = ref<any[]>([])
const version = ref(0)

const showImport = ref(false)
const importing = ref(false)
const impErr = ref('')
const imp = reactive({ source: 'openapi', text: '' })
const impReport = ref<any>(null)

const showEdit = ref(false)
const saving = ref(false)
const editErr = ref('')
const edit = reactive({
  rid: 0, method: '', path: '', code: '',
  rw: 'write', need_data: false,
  mode: 'id_path', idPath: '', fieldPath: '', url: '', pick: '', bindJson: '{}',
  param: '', location: 'query',
})

const showMig = ref(false)
const migBusy = ref(false)
const migErr = ref('')
const mig = reactive({ rid: 0, code: '', newCode: '', confirmed: false, affected: null as any })

async function load() {
  const [d, ad, ob] = await Promise.all([
    api.routes(appId.value),
    api.appDetail(appId.value),
    api.onboardReport(appId.value).catch(() => null),
  ])
  app.value = ad?.app || ad
  items.value = d.items || []
  pending.value = (d.pending || []).map((p: any) => ({ ...p, _edit: false, _code: p.inferred_code }))
  version.value = d.version || 0
  onboard.value = ob
}
async function runOnboard() {
  onboard.value = await api.onboardReport(appId.value).catch((e: any) => { alert('体检失败：' + e.message); return null })
}
function statusTag(st: string): string {
  return st === 'ready' ? 'tag-ok' : st === 'incomplete' ? 'tag-amber' : 'tag-red'
}
function statusText(st: string): string {
  return st === 'ready' ? '可接入' : st === 'incomplete' ? '未完成（有待确认）' : '阻断'
}
onMounted(load)

// ---- 导入 ----
function parseDict(text: string) {
  const entries: any[] = []
  for (const line of text.split('\n')) {
    const t = line.trim()
    if (!t || t.startsWith('#')) continue
    const parts = t.split(/\s+/)
    if (parts.length < 2) continue
    entries.push({ method: parts[0], path: parts[1], action: parts[2] || '' })
  }
  return entries
}
async function doImport() {
  impErr.value = ''
  impReport.value = null
  const body: any =
    imp.source === 'openapi'
      ? { source: 'openapi' }
      : { source: 'dict', entries: parseDict(imp.text) }
  if (body.source === 'dict' && !body.entries.length) {
    impErr.value = '字典为空（每行：METHOD /path [action]）'
    return
  }
  importing.value = true
  try {
    impReport.value = await api.importRoutes(appId.value, body)
    await load()
  } catch (e: any) {
    impErr.value = e.message
  } finally {
    importing.value = false
  }
}

// ---- 待确认队列 ----
async function confirmPending(p: any) {
  try {
    await api.confirmPendingRoute(appId.value, p.id, p._edit ? { code: p._code } : {})
    await load()
  } catch (e: any) {
    alert('落表失败：' + e.message)
  }
}
async function discardPending(p: any) {
  await api.discardPendingRoute(appId.value, p.id)
  await load()
}

// ---- 五格登记 ----
function openEdit(a: any) {
  const m = a.material || {}
  edit.rid = a.id
  edit.method = a.method || ''
  edit.path = a.path || ''
  edit.code = a.code
  edit.rw = rwOf(a) === 'read' ? 'read' : 'write'
  edit.need_data = !!a.need_data
  edit.mode = m.mode || 'id_path'
  edit.idPath = m.path || ''
  edit.fieldPath = m.field_path || ''
  edit.url = m.url || ''
  edit.pick = m.pick || ''
  edit.bindJson = m.bind ? JSON.stringify(m.bind, null, 2) : '{}'
  const sp = a.scope_param || {}
  edit.param = sp.param || ''
  edit.location = sp.location || 'query'
  editErr.value = ''
  showEdit.value = true
}
async function saveEdit() {
  editErr.value = ''
  const body: any = { rw: edit.rw, need_data: edit.need_data }
  if (edit.need_data) {
    const m: any = { mode: edit.mode }
    if (edit.mode === 'id_path') m.path = edit.idPath.trim()
    if (edit.mode === 'envelope') m.field_path = edit.fieldPath.trim() || '.meta.account'
    if (edit.mode === 'fetch_source') {
      m.url = edit.url.trim()
      m.pick = edit.pick.trim()
      try {
        m.bind = JSON.parse(edit.bindJson || '{}')
      } catch {
        editErr.value = 'bind 不是合法 JSON'
        return
      }
    }
    body.material = m
  }
  if (edit.param.trim()) body.scope_param = { param: edit.param.trim(), location: edit.location }
  saving.value = true
  try {
    await api.updateRoute(appId.value, edit.rid, body)
    showEdit.value = false
    await load()
  } catch (e: any) {
    editErr.value = e.message
  } finally {
    saving.value = false
  }
}

// ---- 迁移 / 归档 ----
function openMigrate(a: any) {
  mig.rid = a.id
  mig.code = a.code
  mig.newCode = ''
  mig.confirmed = false
  mig.affected = null
  migErr.value = ''
  showMig.value = true
}
async function doMigrate() {
  migErr.value = ''
  migBusy.value = true
  try {
    const { status, data } = await api.migrateRoute(appId.value, mig.rid, {
      new_code: mig.newCode.trim(),
      confirm: mig.confirmed,
    })
    if (status === 200) {
      showMig.value = false
      await load()
      return
    }
    if (status === 409 && data.affected) {
      mig.affected = data.affected
      migErr.value = '有引用方——勾选确认后重试'
    } else {
      migErr.value = data.error || `HTTP ${status}`
    }
  } finally {
    migBusy.value = false
  }
}
async function archive(a: any) {
  const { status, data } = await api.archiveRoute(appId.value, a.id)
  if (status === 200) {
    await load()
    return
  }
  if (status === 409 && data.affected) {
    const ps = (data.affected.policies || []).map((p: any) => `策略#${p.id} ${p.name}`).join('、')
    const cs = (data.affected.capabilities || []).map((c: any) => `能力包#${c.id} ${c.name}`).join('、')
    alert(`归档被拒——还有引用方：\n${ps}\n${cs}\n先解除引用（归档=可查不可用，不删）`)
    return
  }
  alert(data.error || '归档失败')
}
async function restore(a: any) {
  await api.restoreRoute(appId.value, a.id)
  await load()
}

// ---- 展示辅助 ----
function rwOf(a: any): string {
  if (a.rw === 'read' || a.rw === 'write') return a.rw
  return ['list', 'get', 'read'].includes(a.operation) ? 'read' : 'write'
}
function materialBrief(a: any): string {
  if (!a.need_data) return '—'
  const m = a.material || {}
  if (m.mode === 'id_path') return `id→${m.path || '?'}`
  if (m.mode === 'envelope') return `信封→${m.field_path || '?'}`
  if (m.mode === 'fetch_source') return `回源→${m.pick || '?'}`
  return '★未配'
}
function scopeBrief(a: any): string {
  const s = a.scope_param
  if (!s || !s.param) return '—'
  return `${s.param}@${s.location || 'query'}`
}
</script>

<style scoped>
.rt-page { }
.section-title { display: flex; align-items: center; gap: 10px; font-size: 14px; font-weight: 700; margin: 18px 0 10px; }
.section-hint { font-size: 12px; font-weight: 400; color: var(--text-tertiary); }
.panel { background: var(--bg-card); border: 1px solid var(--border); border-radius: var(--radius); overflow: hidden; }
.rt-wrap { overflow-x: auto; }
.rt-table { width: 100%; border-collapse: collapse; font-size: 13px; }
.rt-table th { text-align: left; padding: 10px 12px; font-size: 11px; text-transform: uppercase; letter-spacing: .04em; color: var(--text-tertiary); background: var(--bg-inset); border-bottom: 1px solid var(--border); white-space: nowrap; }
.rt-table td { padding: 9px 12px; border-bottom: 1px solid var(--border); vertical-align: middle; }
.rt-table tr:last-child td { border-bottom: none; }
.rt-table tr.archived td { opacity: .55; }
.rt-table .code { font-weight: 600; color: var(--brand-strong); }
.mono { font-family: var(--font-mono); font-size: 12px; }
.hint { color: var(--text-secondary); font-size: 12px; }
.empty { padding: 28px; text-align: center; color: var(--text-tertiary); font-size: 13px; }
.tag { font-family: var(--font-mono); font-size: 10px; font-weight: 600; padding: 2px 8px; border-radius: 999px; white-space: nowrap; }
.tag-ok { background: var(--success-bg); color: var(--success); }
.tag-warn { background: var(--warning-bg); color: var(--warning); }
.tag-red { background: var(--danger-bg); color: var(--danger); }
.tag-amber { background: var(--warning-bg); color: var(--warning); }
.tag-blue { background: var(--brand-soft); color: var(--brand-strong); }
.tag-gray { background: var(--bg-inset); color: var(--text-tertiary); border: 1px solid var(--border); }
.btn { display: inline-flex; align-items: center; gap: 5px; height: 30px; padding: 0 12px; border-radius: 8px; font-size: 12px; font-weight: 600; border: 1px solid var(--border); background: var(--bg-card); color: var(--text); cursor: pointer; text-decoration: none; margin-right: 6px; }
.btn:hover { background: var(--bg-hover); border-color: var(--border-strong); }
.btn-sm { height: 26px; padding: 0 8px; font-size: 11px; }
.btn-primary { background: var(--brand); color: #fff; border-color: var(--brand); }
.btn-primary:hover { background: var(--brand-strong); }
.btn-primary:disabled { opacity: .5; cursor: not-allowed; }
.btn-ghost { background: transparent; border-color: transparent; }
.btn-ghost:hover { background: var(--bg-hover); }
.input { width: 100%; padding: 8px 12px; border: 1px solid var(--border); border-radius: 8px; background: var(--bg-card); color: var(--text); font-size: 13px; }
.input:focus { outline: none; border-color: var(--brand); }
.input[readonly] { background: var(--bg-inset); color: var(--text-secondary); }
.input-inline { width: 220px; display: inline-block; margin-right: 6px; padding: 4px 8px; font-size: 12px; }
.modal-mask { position: fixed; inset: 0; background: rgba(0,0,0,.35); display: flex; align-items: center; justify-content: center; z-index: 1000; }
.modal-box { background: var(--bg-card); border: 1px solid var(--border); border-radius: var(--radius); padding: 24px; width: 440px; max-width: 92vw; box-shadow: 0 20px 60px rgba(0,0,0,.2); display: flex; flex-direction: column; gap: 14px; }
.modal-wide { width: 640px; }
.modal-title { font-size: 16px; font-weight: 700; }
.modal-box label { font-size: 13px; font-weight: 600; display: flex; flex-direction: column; gap: 5px; }
.modal-foot { display: flex; gap: 8px; justify-content: flex-end; margin-top: 4px; }
.modal-err { font-size: 12px; color: var(--danger); }
.grid2 { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; }
.radio-row { display: flex; gap: 16px; }
.modal-box .radio { flex-direction: row; align-items: center; gap: 6px; font-weight: 500; }
.check-row { flex-direction: row !important; align-items: center; gap: 8px; font-weight: 500 !important; }
.notice-inline { font-size: 12px; color: var(--text-secondary); background: var(--bg-inset); border: 1px dashed var(--border); border-radius: 8px; padding: 8px 10px; }
.report { border-top: 1px solid var(--border); padding-top: 10px; display: flex; flex-direction: column; gap: 6px; }
.report-line { display: flex; gap: 8px; }
.report-block { font-size: 12px; color: var(--danger); }
.ob-panel { padding: 10px 12px; display: flex; flex-direction: column; gap: 6px; }
.ob-ok { font-size: 12px; color: var(--success); }
.ob-block, .ob-warn { display: flex; align-items: center; gap: 8px; font-size: 12px; flex-wrap: wrap; }
.ob-block .mono { color: var(--danger); }
.ob-warn .mono { color: var(--warning); }
.ob-action { color: var(--brand-strong); }
.ob-reason { color: var(--text-secondary); }
.affected { border: 1px solid rgba(217,119,6,.4); background: var(--warning-bg); border-radius: 8px; padding: 10px 12px; display: flex; flex-direction: column; gap: 6px; }
.affected-title { font-size: 12px; font-weight: 700; color: var(--warning); }
.affected-item { font-size: 12px; color: var(--text-secondary); }
</style>
