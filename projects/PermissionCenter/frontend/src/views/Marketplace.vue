<template>
  <div class="marketplace">
    <!-- 能力市场列表 -->
    <template v-if="!wizard">
      <PageHeader title="能力市场" desc="浏览已发布能力包 → 申请权限（预设 + 主体 + 数据范围，表达式自动生成）">
        <template #actions>
          <router-link to="/app-market" class="btn btn-ghost">🔑 应用市场（接入申请）</router-link>
        </template>
      </PageHeader>

      <div class="filter-bar">
        <input v-model="q" class="search" placeholder="🔍 搜索能力名称、描述、应用、数据模型、标签…" @input="debounced" />
        <select v-model="filterApp" class="filter-select" @change="applyFilter">
          <option value="">全部应用</option>
          <option v-for="a in apps" :key="a.id" :value="a.code">{{ a.name }}（{{ a.code }}）</option>
        </select>
      </div>

      <div class="cap-grid">
        <div v-for="cap in filtered" :key="cap.id" class="cap-card" :data-cap-id="cap.id" @click="startApply(cap)">
          <div class="cap-top">
            <div class="cap-icon" :class="toneOf(cap)">{{ iconOf(cap) }}</div>
            <div style="flex:1;min-width:0;">
              <div class="cap-name">{{ cap.name }}</div>
              <div class="cap-app">{{ cap.app_name }} <span class="mono">· {{ cap.app_code }}</span></div>
            </div>
            <span class="tag tag-blue">已发布 · v{{ cap.version }}</span>
          </div>
          <div class="cap-desc">{{ cap.description }}</div>
          <div class="cap-tags">
            <span v-if="cap.data_model" class="tag tag-gray">{{ cap.data_model }}</span>
            <span v-for="p in cap.presets" :key="p.id" class="tag tag-blue">{{ p.icon || '🔖' }} {{ p.name }}</span>
          </div>
          <div class="cap-foot">
            <span class="cap-badge gray">{{ cap.presets?.length || 0 }} 预设可申请</span>
            <span class="cap-badge green">含数据级</span>
            <button class="btn btn-primary btn-sm" @click.stop="startApply(cap)">📋 申请</button>
          </div>
        </div>
      </div>
      <EmptyState v-if="!filtered.length" text="暂无匹配的能力（应用 owner 需先声明并发布能力）" />
    </template>

    <!-- 申请向导 4 步 -->
    <template v-else>
      <button class="back-link" @click="wizard = false">← 返回能力市场</button>
      <div class="wizard-head">
        <div class="wizard-title">申请「{{ applyCap?.name }}」<span v-if="applyPreset">/ {{ applyPreset.name }}</span></div>
        <div class="wizard-sub">申请人 {{ me?.display_name || me?.username }}（{{ me?.org || '—' }}）</div>
      </div>

      <div class="progress-bar">
        <div v-for="(s, i) in STEPS" :key="i" class="pstep" :class="{ active: step === i + 1, done: step > i + 1 }">
          <div class="pnum">{{ step > i + 1 ? '✓' : i + 1 }}</div><div class="plabel">{{ s }}</div>
        </div>
      </div>

      <div v-if="submitted" class="panel success-card">
        <div class="success-icon">📨</div>
        <div class="success-title">申请已提交</div>
        <div class="success-sub">申请单 #{{ submitted.id }} · {{ submitted.status === 'auto-approved' ? '已自动开通（低风险）' : '待审批' }}</div>
        <div class="btn-row"><router-link to="/requests" class="btn btn-primary">去审批中心查看</router-link><button class="btn" @click="resetWizard">返回市场</button></div>
      </div>

      <div v-else-if="step === 1" class="wizard-body">
        <div class="info-box">🔖 选择要申请的权限组合（预设）——市场只显示已上架预设，点击接口可查看调用契约</div>
        <div class="preset-grid">
          <div v-for="p in applyCap?.presets || []" :key="p.id" class="preset-card" :class="{ selected: applyPreset?.id === p.id, blocked: !eligible(p) }" @click="selectPreset(p)">
            <div class="preset-name">{{ p.icon || '🔖' }} {{ p.name }}</div>
            <div class="preset-line"><span class="badge">{{ (p.grantee_types || []).map((g: string) => GRANTEE[g] || g).join('·') }}</span><span class="badge">{{ scopeBadge(p) }}</span></div>
            <div class="preset-ops">
              <div v-for="op in p.ops || []" :key="op.action" class="op-row" @click.stop="toggleOp(p.id, op.action)">
                <span class="op-method" :class="(op.method || '').toLowerCase()">{{ op.method }}</span>
                <span class="mono op-path">{{ op.path }}</span>
                <span class="op-name">{{ op.name || op.action }}</span>
                <span class="op-chev">{{ expandedOp[p.id] === op.action ? '▾' : '▸' }}</span>
                <div v-if="expandedOp[p.id] === op.action" class="op-ex">
                  <div v-if="op.req_example" class="ex"><div class="ex-t">⬆️ 请求示例</div><pre class="ex-c">{{ op.req_example }}</pre></div>
                  <div v-if="op.resp_example" class="ex"><div class="ex-t">⬇️ 响应示例</div><pre class="ex-c">{{ op.resp_example }}</pre></div>
                  <div v-if="!op.req_example && !op.resp_example" class="ex-empty">（暂无示例）</div>
                </div>
              </div>
            </div>
            <div v-if="p.data_control" class="data-badge">数据级: {{ (p.data_models || []).join(',') }}</div>
            <div v-if="!eligible(p)" class="block-hint">🚫 该预设的可申请范围与你不符（{{ scopeDesc(p) }}）。<br />💡 可申请同能力的「查看类」预设，或联系负责人。</div>
          </div>
        </div>
      </div>

      <div v-else-if="step === 2" class="wizard-body">
        <div v-if="appOnly" class="info-box orange">该预设<b>仅限程序主体</b>——程序无法自己操作，由应用 owner（人）代理申请，因此只能选择「下游应用」。</div>
        <div v-else class="info-box blue">该预设允许主体：<b>{{ (applyPreset?.grantee_types || []).map((g: string) => GRANTEE[g] || g).join(' / ') }}</b></div>
        <div class="subject-grid">
          <div v-for="t in SUBJECTS" :key="t.v" class="subject-card" :class="{ selected: granteeType === t.v, locked: !granteeEnabled(t.v) }" @click="granteeEnabled(t.v) && (granteeType = t.v, granteeDetail = '', loadGranteeItems(t.v))">
            <div class="subj-icon">{{ t.icon }}</div><div class="subj-name">{{ t.name }}</div><div class="subj-desc">{{ t.desc }}</div>
            <div class="subj-badge">{{ granteeEnabled(t.v) ? '可选' : '不可选' }}</div>
          </div>
        </div>
        <div v-if="granteeType === 'app'" class="dual-box">
          🔀 双主体：grantee = <b>应用本身</b>（程序身份）· applicant = <b>{{ me?.display_name || me?.username }}</b>（应用 owner 人代理）
          <div v-if="granteeDetail && !onboardedFor(granteeDetail)" class="onboard-hint">⚠️ 该下游应用尚未接入「{{ appName(applyCap?.app_id) }}」——可先到 <router-link to="/app-market" class="link">应用市场</router-link> 完成接入申请（凭证一次签发），能力包申请自动复用。</div>
          <div v-else-if="granteeDetail && onboardedFor(granteeDetail)" class="onboard-ok">✅ 已接入（凭证已签发），本次申请将复用凭证、仅追加 scope。</div>
        </div>
        <div v-if="granteeItems.length" class="grantee-list">
          <div class="grantee-title">选择{{ granteeType === 'app' ? '下游应用' : granteeType === 'org' ? '组织' : granteeType === 'group' ? '自建组' : '用户' }}：</div>
          <div v-for="it in granteeItems" :key="it.value" class="grantee-item" :class="{ selected: granteeDetail === it.value }" @click="granteeDetail = it.value">
            <div class="radio"></div><div class="sel-name">{{ it.name }}</div><div class="sel-meta mono">{{ it.meta }}</div>
          </div>
        </div>
      </div>

      <div v-else-if="step === 3" class="wizard-body">
        <div v-if="!applyPreset?.data_control" class="info-box green">✅ 该预设未开启数据级控制：接口可访问全部数据。</div>
        <template v-else>
          <div class="card-desc">该预设开启数据级控制，请为每个数据模型选择数据范围（选择后自动生成表达式）。</div>
          <div v-for="mc in applyPreset?.data_models || []" :key="mc" class="dim-row">
            <div class="dim-head"><b class="mono">{{ mc }}</b><span class="badge">数据范围</span></div>
            <div class="scope-opts">
              <div v-for="o in optionsOf(mc)" :key="o.type" class="scope-opt" :class="{ selected: scopeOf(mc).type === o.type }" @click="selectScopeType(mc, o.type)">
                <div class="so-icon">{{ SCOPE_ICON[o.type] }}</div><div><div class="so-name">{{ o.label }}</div><div class="so-desc">{{ o.desc || '' }}</div></div>
              </div>
            </div>
            <div class="scope-form">
              <template v-if="scopeOf(mc).type === 'all'"><div class="info-box cyan">该模型全部数据（无需填写）</div></template>
              <template v-else-if="scopeOf(mc).type === 'instance'">
                <label class="field-label">选择实例</label>
                <div class="inst-list"><label v-for="i in instancesOf(mc)" :key="i.id" class="check"><input type="checkbox" :checked="scopeOf(mc).selectedValues.includes(String(i.id))" @change="toggleInstance(mc, i)" /> {{ i.name }} <span class="mono text-secondary">{{ i.id }}</span></label></div>
              </template>
              <template v-else-if="scopeOf(mc).type === 'select'">
                <label class="field-label">{{ optOf(mc, 'select')?.label }}（单选）</label>
                <div class="choice-chips"><div v-for="ch in optOf(mc, 'select')?.choices || []" :key="ch.value" class="choice-chip" :class="{ selected: scopeOf(mc).selectedValue === ch.value }" @click="scopeOf(mc).selectedValue = ch.value; scopeOf(mc).selectedValues = []"><span class="cc-label">{{ ch.label }}</span><span class="cc-value">{{ ch.value }}</span></div></div>
              </template>
              <template v-else-if="scopeOf(mc).type === 'multi_select'">
                <label class="field-label">{{ optOf(mc, 'multi_select')?.label }}（可多选）</label>
                <div class="choice-chips"><div v-for="ch in optOf(mc, 'multi_select')?.choices || []" :key="ch.value" class="choice-chip" :class="{ selected: scopeOf(mc).selectedValues.includes(ch.value) }" @click="toggleValue(mc, ch.value)"><span class="cc-label">{{ ch.label }}</span><span class="cc-value">{{ ch.value }}</span></div></div>
              </template>
              <template v-else-if="scopeOf(mc).type === 'variable'"><div class="var-display">🔄 自动匹配：<b>{{ optOf(mc, 'variable')?.var_label || optOf(mc, 'variable')?.variable }}</b> → 运行时按 grantee（权限作用主体）解析，无需手动填写</div></template>
              <template v-else-if="scopeOf(mc).type === 'input'"><label class="field-label">{{ optOf(mc, 'input')?.label }}（自由填写）</label><input class="input" :placeholder="optOf(mc, 'input')?.placeholder || '请输入...'" :value="scopeOf(mc).selectedValue" @input="onScopeInput(mc, $event)" /></template>
            </div>
            <div v-if="autoExpr(mc)" class="expr-preview">生成表达式：<b>{{ autoExpr(mc) }}</b></div>
          </div>
        </template>
      </div>

      <div v-else class="wizard-body">
        <div v-if="preview">
          <div class="preview-sec"><div class="ps-head">👤 申请主体（双主体）</div><div class="ps-body"><div class="prow"><span class="pk">授权主体</span><span class="pv">{{ granteeLabel() }}</span></div><div class="prow"><span class="pk">申请人</span><span class="pv">{{ me?.display_name || me?.username }} · applicant = 人代理</span></div></div></div>
          <div class="preview-sec"><div class="ps-head">📦 能力基本信息</div><div class="ps-body"><div class="prow"><span class="pk">能力包</span><span class="pv">{{ applyCap?.name }}</span></div><div class="prow"><span class="pk">所属应用</span><span class="pv">{{ appName(applyCap?.app_id) }}</span></div></div></div>
          <div class="preview-sec"><div class="ps-head">🎯 申请的预设</div><div class="ps-body"><div class="prow"><span class="pk">预设</span><span class="pv"><b>{{ applyPreset?.name }}</b></span></div><div class="prow"><span class="pk">数据范围</span><span class="pv">{{ scopeText }}</span></div></div></div>
          <div class="preview-sec"><div class="ps-head">📡 接口明细（程序对接契约）</div><div class="ps-body">
            <div v-for="op in applyPreset?.ops || []" :key="op.action" class="op-row" @click.stop="toggleOp('preview', op.action)">
              <span class="op-method" :class="(op.method || '').toLowerCase()">{{ op.method }}</span>
              <span class="mono op-path">{{ op.path }}</span>
              <span class="op-name">{{ op.name || op.action }}</span>
              <span class="op-chev">{{ expandedOp['preview'] === op.action ? '▾' : '▸' }}</span>
              <div v-if="expandedOp['preview'] === op.action" class="op-ex">
                <div v-if="op.req_example" class="ex"><div class="ex-t">⬆️ 请求示例</div><pre class="ex-c">{{ op.req_example }}</pre></div>
                <div v-if="op.resp_example" class="ex"><div class="ex-t">⬇️ 响应示例</div><pre class="ex-c">{{ op.resp_example }}</pre></div>
                <div v-if="!op.req_example && !op.resp_example" class="ex-empty">（暂无示例）</div>
              </div>
            </div>
          </div></div>
          <div class="preview-sec"><div class="ps-head">🔐 权限表达式（Casbin + OpenFGA）</div><div class="ps-body"><pre class="codeblock">{{ preview.expression?.code || '—' }}</pre></div></div>
          <div class="info-box purple">审批链：{{ (preview.approval_chain || []).map((a: any) => a.role).join(' → ') }}</div>
          <div class="btn-row"><button class="btn btn-primary" @click="submit" :disabled="submitting">{{ submitting ? '提交中…' : '🚀 发起审批' }}</button></div>
        </div>
        <div v-else class="empty-state">预览加载中…</div>
      </div>

      <div class="btn-row wizard-nav" v-if="!submitted">
        <button class="btn" v-if="step > 1" @click="step--">← 上一步</button>
        <button class="btn btn-primary" v-if="step < 4" @click="next" :disabled="!canNext">下一步 →</button>
      </div>
    </template>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import { api } from '../api/client'
import { ElMessage } from 'element-plus'
import PageHeader from '../components/PageHeader.vue'
import EmptyState from '../components/EmptyState.vue'

const STEPS = ['选择预设', '选择主体', '数据范围', '预览审批']
const route = useRoute()
const GRANTEE: Record<string, string> = { user: '用户', org: '组织', group: '自建组', app: '程序' }
const SUBJECTS = [
  { v: 'user', icon: '👤', name: '我自己', desc: '为自己申请' },
  { v: 'org', icon: '🏢', name: '组织', desc: '为所在组织申请' },
  { v: 'group', icon: '👥', name: '自建组', desc: '为自建组申请' },
  { v: 'app', icon: '🔌', name: '下游应用', desc: '为应用（程序身份）申请' },
]
const SCOPE_LABEL: Record<string, string> = { all: '所有数据', instance: '具体实例', select: '单选', multi_select: '多选', variable: '自动匹配', input: '自由输入' }
const SCOPE_ICON: Record<string, string> = { all: '🌍', instance: '📌', select: '📋', multi_select: '☑️', variable: '🔄', input: '⌨️' }

const caps = ref<any[]>([])
const apps = ref<any[]>([])
const me = ref<any>(null)
const myRequests = ref<any[]>([])
const q = ref('')
const filterApp = ref('')
const wizard = ref(false)
const applyCap = ref<any>(null)
const applyPreset = ref<any>(null)
const granteeType = ref('')
const granteeDetail = ref('')
const granteeItems = ref<any[]>([])
const step = ref(1)
// 接口契约展开状态（key=预设 id 或 'preview'，value=展开的 action）
const expandedOp = ref<Record<string, string>>({})
function toggleOp(key: string, action: string) {
  expandedOp.value[key] = expandedOp.value[key] === action ? '' : action
}
const submitted = ref<any>(null)
const submitting = ref(false)
const preview = ref<any>(null)
const scopeSel = ref<Record<string, any>>({})
const instMap = ref<Record<string, any[]>>({})
const groups = ref<any[]>([])
const optCache = ref<Record<string, any[]>>({})

const filtered = computed(() => {
  const k = q.value.trim().toLowerCase()
  return caps.value.filter((c: any) => {
    if (filterApp.value && c.app_code !== filterApp.value) return false
    if (!k) return true
    return (c.name + c.description + (c.app_name || '') + (c.data_model || '')).toLowerCase().includes(k)
  })
})

function appName(id: number) { return apps.value.find(a => a.id === id)?.name || `#${id}` }
function iconOf(c: any) { return c.name.includes('主机') ? '🖥️' : c.name.includes('数据库') ? '🗄️' : c.name.includes('资源') ? '☁️' : '📦' }
function toneOf(c: any) { return c.name.includes('主机') ? 'blue' : c.name.includes('数据库') ? 'amber' : 'cyan' }

function scopeBadge(p: any) { const s = p.apply_scope || {}; if (!s.orgs?.length && !s.people?.length) return '范围: 全员'; const parts: string[] = []; if (s.orgs?.length) parts.push('仅 ' + s.orgs[0].split(' → ').pop()); if (s.people?.length) parts.push(s.people.length + ' 人'); return '范围: ' + parts.join(' · ') }
function scopeDesc(p: any) { const s = p.apply_scope || {}; const parts: string[] = []; if (s.orgs?.length) parts.push(s.orgs.map((o: string) => o.split(' → ').pop()).join(',')); if (s.people?.length) parts.push(s.people.length + '人'); return parts.join(' · ') || '全员' }
function eligible(p: any) { const s = p.apply_scope || {}; return (!s.orgs?.length || s.orgs.includes(me.value?.org)) && (!s.people?.length || s.people.includes(me.value?.username)) }
function granteeEnabled(v: string) { return (applyPreset.value?.grantee_types || []).includes(v) }
const appOnly = computed(() => applyPreset.value?.grantee_types?.length === 1 && applyPreset.value?.grantee_types[0] === 'app')

function optionsOf(mc: string) { return optCache.value[`${applyCap.value?.id}_${applyPreset.value?.id}_${mc}`] || [] }
function optOf(mc: string, type: string) { return optionsOf(mc).find((o: any) => o.type === type) }
function scopeOf(mc: string) { if (!scopeSel.value[mc]) scopeSel.value[mc] = { type: optionsOf(mc)[0]?.type || 'all', selectedValue: '', selectedValues: [] as string[] }; return scopeSel.value[mc] }
function selectScopeType(mc: string, type: string) { const s = scopeOf(mc); s.type = type; s.selectedValue = ''; s.selectedValues = [] }
function toggleValue(mc: string, v: string) { const s = scopeOf(mc); const i = s.selectedValues.indexOf(v); i < 0 ? s.selectedValues.push(v) : s.selectedValues.splice(i, 1) }
function toggleInstance(mc: string, inst: any) { const s = scopeOf(mc); const id = String(inst.id); const i = s.selectedValues.indexOf(id); i < 0 ? s.selectedValues.push(id) : s.selectedValues.splice(i, 1) }
function onScopeInput(mc: string, e: Event) { scopeOf(mc).selectedValue = (e.target as HTMLInputElement).value }
function autoExpr(mc: string) {
  const s = scopeOf(mc); const o = optOf(mc, s.type); if (!o) return ''
  switch (s.type) {
    case 'select': return s.selectedValue ? `${o.field} ${o.op} "${s.selectedValue}"` : ''
    case 'multi_select': return s.selectedValues.length ? `${o.field} ${o.op} [${s.selectedValues.map(v => '"' + v + '"').join(', ')}]` : ''
    case 'variable': return `${o.field} ${o.op} "${o.variable}"`
    case 'input': return s.selectedValue ? `${o.field} ${o.op} "${s.selectedValue}"` : ''
  }
  return ''
}
function scopeSelectionsPayload() { const out: any[] = []; for (const mc of applyPreset.value?.data_models || []) { const s = scopeOf(mc); out.push({ model: mc, type: s.type, selectedValue: s.selectedValue, selectedValues: s.selectedValues }) } return out }
const scopeText = computed(() => scopeSelectionsPayload().map(s => `${s.model}: ${SCOPE_LABEL[s.type] || s.type}`).join(' · '))

async function loadInstances(mc: string) {
  if (instMap.value[mc]) return
  try {
    const models = ((await api.resourceModels()) as any).items || []
    const rm = models.find((m: any) => m.code === mc)
    instMap.value[mc] = rm ? (((await api.instances(rm.id)) as any).items || []).map((i: any) => ({ id: i.id, name: i.name })) : []
  } catch { instMap.value[mc] = [] }
}
function instancesOf(mc: string) { return instMap.value[mc] || [] }

async function loadScopeOptions() {
  const cid = applyCap.value?.id, pid = applyPreset.value?.id
  if (!cid || !pid) return
  scopeSel.value = {}
  for (const mc of applyPreset.value?.data_models || []) {
    const key = `${cid}_${pid}_${mc}`
    try { const r: any = await api.presetScopeOptions(cid, pid, mc); optCache.value[key] = (r.options || []).map((o: any) => ({ ...o, choices: o.choices || [] })) } catch { optCache.value[key] = [] }
    await loadInstances(mc)
  }
}

async function loadGranteeItems(v: string) {
  granteeItems.value = []
  if (v === 'app') granteeItems.value = apps.value.filter(a => a.id !== applyCap.value?.app_id).map(a => ({ name: a.name, meta: `${a.code}`, value: String(a.id) }))
  else if (v === 'org' || v === 'group') granteeItems.value = groups.value.filter((g: any) => (v === 'org' ? g.type === 1 : g.type !== 1)).map((g: any) => ({ name: g.name, meta: g.parent_path || '', value: String(g.id) }))
  else if (v === 'user') granteeItems.value = [{ name: me.value?.display_name || me.value?.username, meta: me.value?.username, value: 'me' }]
}
function granteeLabel() {
  if (granteeType.value === 'app') { const a = apps.value.find(x => String(x.id) === granteeDetail.value); return a ? `${a.name}（client:${a.code}）` : granteeDetail.value }
  const item = granteeItems.value.find(i => i.value === granteeDetail.value)
  return `${GRANTEE[granteeType.value] || granteeType.value} · ${item?.name || granteeDetail.value}`
}
function granteeId() { return granteeType.value === 'user' ? me.value?.id : Number(granteeDetail.value) || 0 }
function onboardedFor(consumerAppId: string) { return myRequests.value.some((r: any) => r.request_type === 3 && r.status === 2 && r.content?.provider_app_id === applyCap.value?.app_id && String(r.content?.consumer_app_id) === consumerAppId) }

function startApply(cap: any, presetId?: string) {
  applyCap.value = cap; applyPreset.value = null; granteeType.value = ''; granteeDetail.value = ''; scopeSel.value = {}; submitted.value = null; preview.value = null; step.value = 1; wizard.value = true
  if (presetId) { const p = (cap.presets || []).find((x: any) => x.id === presetId); if (p && eligible(p)) selectPreset(p) }
}
function selectPreset(p: any) { if (!eligible(p)) return; applyPreset.value = p; step.value = 2; loadScopeOptions() }
function resetWizard() { wizard.value = false; applyCap.value = null; applyPreset.value = null }
const canNext = computed(() => { if (step.value === 1) return !!applyPreset.value; if (step.value === 2) return !!granteeDetail.value; return true })
function next() { if (step.value === 3) loadPreview(); if (canNext.value) step.value++ }
watch(step, async (s) => { if (s === 3) await loadScopeOptions(); if (s === 4) await loadPreview() })

async function loadPreview() {
  preview.value = null
  try {
    preview.value = await api.previewRequest({
      app_id: applyCap.value?.app_id,
      subject_type: granteeType.value === 'app' ? 4 : granteeType.value === 'org' ? 3 : granteeType.value === 'group' ? 2 : 1,
      subject_id: granteeId(),
      capability_id: applyCap.value?.id, preset_id: applyPreset.value?.id,
      grantee_type: granteeType.value,
      grantee_name: granteeType.value === 'app' ? 'client:' + (apps.value.find(a => String(a.id) === granteeDetail.value)?.code || granteeDetail.value) : '',
      grantee_id: granteeId(),
      scope_selections: scopeSelectionsPayload(),
    })
  } catch (e: any) { ElMessage.error(e.message) }
}
async function submit() {
  submitting.value = true
  try {
    submitted.value = await api.submitRequest({
      app_id: applyCap.value?.app_id,
      subject_type: granteeType.value === 'app' ? 4 : granteeType.value === 'org' ? 3 : granteeType.value === 'group' ? 2 : 1,
      subject_id: granteeId(),
      capability_id: applyCap.value?.id, preset_id: applyPreset.value?.id,
      grantee_type: granteeType.value,
      grantee_name: granteeType.value === 'app' ? 'client:' + (apps.value.find(a => String(a.id) === granteeDetail.value)?.code || granteeDetail.value) : '',
      grantee_id: granteeId(),
      scope_selections: scopeSelectionsPayload(),
      reason: `申请「${applyCap.value?.name} / ${applyPreset.value?.name}」`,
    })
  } catch (e: any) { ElMessage.error(e.message) } finally { submitting.value = false }
}

let timer: any = null
function debounced() { clearTimeout(timer); timer = setTimeout(() => { /* computed reacts to q */ }, 200) }
function applyFilter() { /* computed reacts */ }

onMounted(async () => {
  try {
    const [appsData, capData, meData, groupData] = await Promise.all([api.marketplaceApps(), api.marketplaceCapabilities(), api.me(), api.groups()])
    apps.value = (appsData as any).items || []
    caps.value = (capData as any).items || []
    me.value = (meData as any).user || meData
    groups.value = ((groupData as any).items || [])
    myRequests.value = ((await api.requests()) as any).items || []
  } catch (e: any) { ElMessage.error(e.message) }
  // 能力包深链：?cap_id= 定位并高亮
  const capId = Number(route.query.cap_id)
  if (capId) {
    setTimeout(() => {
      const el: HTMLElement | null = document.querySelector(`[data-cap-id="${capId}"]`)
      el?.scrollIntoView({ behavior: 'smooth', block: 'center' })
      el?.classList.add('flash')
      setTimeout(() => el?.classList.remove('flash'), 2600)
    }, 600)
  }
})
</script>

<style scoped>
.marketplace { }
.back-link { font-size: 13px; color: var(--text-secondary); background: none; border: none; cursor: pointer; display: block; margin-bottom: 8px; }
.filter-bar { display: flex; gap: 8px; padding: 12px 16px; background: var(--bg-card); border: 1px solid var(--border); border-radius: var(--radius); margin-bottom: 16px; }
.search { flex: 1; height: 34px; padding: 0 12px; background: var(--bg-inset); border: 1px solid var(--border); border-radius: 8px; color: var(--text); font-size: 13px; }
.filter-select { height: 34px; padding: 0 10px; border: 1px solid var(--border); border-radius: 8px; background: var(--bg-card); color: var(--text); font-size: 13px; }
.cap-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(320px, 1fr)); gap: 16px; }
.cap-card { background: var(--bg-card); border: 1px solid var(--border); border-radius: var(--radius); padding: 16px; box-shadow: var(--shadow-sm); cursor: pointer; transition: all .18s; }
.cap-card:hover { border-color: var(--brand); box-shadow: var(--shadow-md); transform: translateY(-2px); }
.cap-card.flash { border-color: var(--brand); box-shadow: 0 0 0 3px rgba(47,111,237,.25), var(--shadow-md); }
.cap-top { display: flex; align-items: center; gap: 12px; margin-bottom: 10px; }
.cap-icon { width: 40px; height: 40px; border-radius: 10px; display: flex; align-items: center; justify-content: center; font-size: 18px; flex-shrink: 0; }
.cap-icon.blue { background: var(--brand-soft); }
.cap-icon.amber { background: var(--warning-bg); }
.cap-icon.cyan { background: var(--info-bg); }
.cap-name { font-size: 15px; font-weight: 600; }
.cap-app { font-size: 12px; color: var(--text-tertiary); }
.cap-desc { font-size: 13px; color: var(--text-secondary); margin-bottom: 12px; }
.cap-tags { display: flex; gap: 6px; flex-wrap: wrap; }
.cap-foot { display: flex; align-items: center; gap: 8px; margin-top: 12px; padding-top: 12px; border-top: 1px solid var(--border); }
.cap-badge { padding: 2px 8px; border-radius: 6px; font-size: 11px; }
.cap-badge.gray { background: var(--bg-inset); color: var(--text-secondary); border: 1px solid var(--border); }
.cap-badge.green { background: var(--success-bg); color: var(--success); }
.wizard-head { margin-bottom: 12px; }
.wizard-title { font-size: 17px; font-weight: 700; }
.wizard-sub { font-size: 12px; color: var(--text-secondary); }
.progress-bar { display: flex; gap: 6px; margin-bottom: 16px; padding: 12px 16px; background: var(--bg-card); border: 1px solid var(--border); border-radius: var(--radius); }
.pstep { display: flex; align-items: center; gap: 8px; flex: 1; }
.pnum { width: 24px; height: 24px; border-radius: 50%; border: 2px solid var(--border); display: inline-flex; align-items: center; justify-content: center; font-size: 12px; font-weight: 700; color: var(--text-tertiary); }
.pstep.active .pnum { background: var(--brand); border-color: var(--brand); color: #fff; }
.pstep.done .pnum { background: var(--success-bg); border-color: var(--success); color: var(--success); }
.plabel { font-size: 12px; color: var(--text-tertiary); font-weight: 600; }
.pstep.active .plabel { color: var(--text); }
.wizard-body { min-height: 200px; }
.preset-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)); gap: 12px; }
.preset-card { background: var(--bg-card); border: 2px solid var(--border); border-radius: var(--radius); padding: 14px; cursor: pointer; }
.preset-card.selected { border-color: var(--brand); }
.preset-card.blocked { opacity: .65; }
.preset-name { font-size: 14px; font-weight: 700; margin-bottom: 8px; }
.preset-line { display: flex; gap: 6px; flex-wrap: wrap; }
.preset-ops { display: flex; flex-direction: column; gap: 4px; margin-top: 8px; }
.op-item { padding: 2px 6px; background: var(--bg-inset); border: 1px solid var(--border); border-radius: 4px; font-size: 11px; }

/* 接口契约明细（v12） */
.op-row { display: flex; align-items: center; gap: 8px; flex-wrap: wrap; padding: 5px 8px; border: 1px solid var(--border); border-radius: 6px; background: var(--bg-inset); cursor: pointer; font-size: 12px; }
.op-row:hover { border-color: var(--brand); }
.op-method { font-family: var(--font-mono); font-size: 10px; font-weight: 700; padding: 1px 5px; border-radius: 3px; }
.op-method.get { background: var(--info-bg, #cffafe); color: var(--info, #0891b2); }
.op-method.post { background: var(--success-bg, #dcfce7); color: var(--success, #16a34a); }
.op-method.put, .op-method.patch { background: var(--warning-bg, #fef3c7); color: var(--warning, #d97706); }
.op-method.delete { background: rgba(239,68,68,.12); color: #dc2626; }
.op-path { color: var(--text); font-size: 12px; }
.op-name { color: var(--text-secondary); font-size: 12px; flex: 1; min-width: 80px; }
.op-chev { color: var(--text-tertiary); font-size: 10px; }
.op-ex { width: 100%; margin-top: 4px; display: flex; flex-direction: column; gap: 6px; }
.ex { display: flex; flex-direction: column; gap: 3px; }
.ex-t { font-size: 11px; font-weight: 600; color: var(--text-tertiary); }
.ex-c { font-family: var(--font-mono); font-size: 11px; background: var(--bg-secondary); border: 1px solid var(--border); border-radius: 4px; padding: 6px 8px; white-space: pre-wrap; word-break: break-all; margin: 0; }
.ex-empty { font-size: 11px; color: var(--text-tertiary); }
.data-badge { margin-top: 8px; font-size: 11px; color: var(--text-secondary); }
.block-hint { margin-top: 8px; font-size: 11px; color: var(--warning); background: var(--warning-bg); padding: 8px; border-radius: 6px; }
.subject-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(200px, 1fr)); gap: 12px; }
.subject-card { background: var(--bg-card); border: 2px solid var(--border); border-radius: var(--radius); padding: 16px; cursor: pointer; }
.subject-card.selected { border-color: var(--brand); }
.subject-card.locked { opacity: .45; pointer-events: none; }
.subj-icon { font-size: 22px; }
.subj-name { font-size: 14px; font-weight: 700; margin: 6px 0 4px; }
.subj-desc { font-size: 12px; color: var(--text-secondary); }
.subj-badge { margin-top: 8px; font-size: 11px; color: var(--text-tertiary); }
.dual-box { margin-top: 12px; padding: 10px 14px; background: var(--bg-inset); border: 1px solid var(--border); border-radius: 8px; font-size: 12px; }
.onboard-hint { margin-top: 8px; font-size: 11px; color: var(--warning); }
.onboard-ok { margin-top: 8px; font-size: 11px; color: var(--success); }
.link { color: var(--brand); }
.grantee-list { margin-top: 14px; }
.grantee-title { font-size: 13px; font-weight: 600; margin-bottom: 8px; }
.grantee-item { display: flex; align-items: center; gap: 10px; padding: 10px 12px; border: 1px solid var(--border); border-radius: 8px; margin-bottom: 6px; cursor: pointer; background: var(--bg-card); }
.grantee-item.selected { border-color: var(--brand); }
.radio { width: 12px; height: 12px; border-radius: 50%; border: 2px solid var(--border); }
.grantee-item.selected .radio { border-color: var(--brand); background: var(--brand); }
.sel-name { font-size: 13px; font-weight: 600; }
.sel-meta { font-size: 11px; color: var(--text-tertiary); }
.dim-row { background: var(--bg-card); border: 1px solid var(--border); border-radius: var(--radius); padding: 12px; margin-bottom: 12px; }
.dim-head { display: flex; align-items: center; gap: 10px; margin-bottom: 10px; }
.scope-opts { display: flex; flex-direction: column; gap: 8px; }
.scope-opt { display: flex; gap: 12px; padding: 12px 14px; border: 2px solid var(--border); border-radius: 8px; cursor: pointer; background: var(--bg-card); }
.scope-opt.selected { border-color: var(--brand); background: var(--brand-softer); }
.so-icon { font-size: 20px; }
.so-name { font-size: 13px; font-weight: 700; }
.so-desc { font-size: 11px; color: var(--text-secondary); }
.scope-form { margin-top: 10px; padding: 12px; background: var(--bg-inset); border: 1px solid var(--border); border-radius: 8px; }
.field-label { display: block; font-size: 13px; font-weight: 600; margin-bottom: 6px; }
.choice-chips { display: flex; flex-wrap: wrap; gap: 6px; }
.choice-chip { display: inline-flex; align-items: center; gap: 4px; padding: 5px 12px; border: 2px solid var(--border); border-radius: 8px; font-size: 12px; cursor: pointer; background: var(--bg-card); }
.choice-chip.selected { border-color: var(--brand); background: var(--brand-soft); font-weight: 600; }
.cc-value { font-family: var(--font-mono); color: var(--text-tertiary); font-size: 11px; }
.inst-list { display: flex; flex-direction: column; gap: 6px; }
.check { display: inline-flex; align-items: center; gap: 6px; font-size: 12px; cursor: pointer; }
.var-display { padding: 10px 14px; background: var(--bg-card); border: 1px solid var(--border); border-radius: 8px; font-size: 12px; }
.input { width: 100%; padding: 7px 10px; border: 1px solid var(--border); border-radius: 8px; background: var(--bg-card); color: var(--text); font-size: 13px; }
.expr-preview { margin-top: 8px; padding: 8px 12px; background: var(--bg-card); border: 1px solid var(--border); border-radius: 6px; font-family: var(--font-mono); font-size: 12px; }
.preview-sec { background: var(--bg-card); border: 1px solid var(--border); border-radius: var(--radius); margin-bottom: 10px; overflow: hidden; }
.ps-head { padding: 9px 12px; background: var(--bg-inset); font-size: 13px; font-weight: 700; border-bottom: 1px solid var(--border); }
.ps-body { padding: 10px 12px; }
.prow { display: flex; gap: 8px; padding: 4px 0; font-size: 12px; }
.pk { flex: 0 0 90px; color: var(--text-tertiary); }
.pv { flex: 1; }
.codeblock { background: var(--bg-inset); border: 1px solid var(--border); border-radius: 8px; padding: 12px; font-family: var(--font-mono); font-size: 12px; white-space: pre-wrap; }
.info-box { padding: 10px 14px; background: var(--bg-inset); border: 1px solid var(--border); border-radius: 8px; font-size: 12px; margin-bottom: 12px; }
.info-box.orange { background: var(--warning-bg); border-color: rgba(217,119,6,.3); color: var(--warning); }
.info-box.blue { background: var(--brand-softer); border-color: rgba(47,111,237,.3); color: var(--brand-strong); }
.info-box.green { background: var(--success-bg); border-color: rgba(22,163,74,.3); color: var(--success); }
.info-box.cyan { background: var(--info-bg); border-color: rgba(8,145,178,.3); color: var(--info); }
.info-box.purple { background: var(--purple-bg); border-color: rgba(124,58,237,.3); color: var(--purple); }
.card-desc { font-size: 12px; color: var(--text-secondary); margin-bottom: 12px; }
.btn-row { display: flex; gap: 10px; margin-top: 14px; }
.wizard-nav { justify-content: space-between; }
.btn { display: inline-flex; align-items: center; gap: 6px; height: 34px; padding: 0 14px; border-radius: 8px; font-size: 13px; font-weight: 600; border: 1px solid var(--border); background: var(--bg-card); color: var(--text); cursor: pointer; text-decoration: none; }
.btn:hover { background: var(--bg-hover); }
.btn-primary { background: var(--brand); color: #fff; border-color: var(--brand); }
.btn-primary:hover { background: var(--brand-strong); }
.btn-ghost { background: transparent; color: var(--text-secondary); }
.btn-sm { height: 30px; padding: 0 12px; font-size: 12px; }
.btn:disabled { opacity: .5; cursor: not-allowed; }
.success-card { text-align: center; padding: 40px 20px; background: var(--bg-card); border: 1px solid var(--border); border-radius: var(--radius); }
.success-icon { font-size: 40px; }
.success-title { font-size: 18px; font-weight: 700; margin: 10px 0 4px; }
.success-sub { font-size: 13px; color: var(--text-secondary); margin-bottom: 20px; }
.success-card .btn-row { justify-content: center; }
.badge { display: inline-flex; align-items: center; gap: 4px; padding: 2px 9px; border: 1px solid var(--border); border-radius: 999px; font-size: 11px; font-weight: 600; background: var(--bg-inset); }
.tag { font-family: var(--font-mono); font-size: 10px; font-weight: 600; padding: 2px 8px; border-radius: 999px; }
.tag-blue { background: var(--brand-soft); color: var(--brand-strong); }
.tag-gray { background: var(--bg-inset); color: var(--text-tertiary); border: 1px solid var(--border); }
.empty-state { padding: 40px; text-align: center; color: var(--text-tertiary); font-size: 13px; }
.mono { font-family: var(--font-mono); font-size: 12px; }
.text-secondary { color: var(--text-secondary); }
</style>
