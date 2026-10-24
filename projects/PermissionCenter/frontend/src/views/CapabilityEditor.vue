<template>
  <div class="cap-editor" v-if="cap">
    <header class="page-header">
      <router-link :to="`/apps/${appId}`" class="back-link">← 返回应用详情</router-link>
      <h1>
        <span class="mono">{{ cap.name }}</span>
        <span class="tag" :class="viewOnly ? 'tag-warn' : 'tag-ok'">{{ viewOnly ? '查看模式（只读）' : '编辑模式' }}</span>
      </h1>
      <span class="page-desc">{{ app?.app?.name }} · v{{ cap.version }} · {{ cap.status === 'published' ? '已发布' : '草稿' }}</span>
    </header>

    <!-- ① 基本信息 -->
    <div class="section-title"><span class="sec-accent">①</span> 基本信息</div>
    <div class="card form-grid">
      <label>能力名称
        <input v-model="form.name" :disabled="viewOnly" class="input" />
      </label>
      <label>版本
        <input :value="'v' + cap.version" disabled class="input" />
      </label>
      <label>所属应用
        <span class="app-badge">{{ app?.app?.name || '—' }}<span class="app-code">{{ app?.app?.code }}</span></span>
      </label>
      <label>标签
        <div class="chip-row">
          <span v-for="t in ALL_TAGS" :key="t" class="chip" :class="{ on: form.tags.includes(t) }"
            @click="!viewOnly && toggleTag(t)">{{ t }}</span>
        </div>
      </label>
      <label class="span2">能力描述
        <textarea v-model="form.description" :disabled="viewOnly" rows="2" class="input" placeholder="一句话描述该能力…" />
      </label>
      <label>👁️ 可见性
        <select v-model="form.visibility" :disabled="viewOnly" class="input">
          <option value="public">全员可见（public）</option>
          <option value="org_visible">仅指定组织可见（org_visible）</option>
          <option value="hidden">隐身（hidden）</option>
        </select>
      </label>
      <div class="field-full">
        <label>🎯 默认可申请主体</label>
        <p class="field-hint">设定市场中哪些类型的主体可以申请此能力包</p>
        <div class="chip-row">
          <span v-for="g in GRANTEE_OPTIONS" :key="g.v" class="chip" :class="{ on: form.grantee_types.includes(g.v) }"
            @click="!viewOnly && toggleGrantee(g.v)">{{ g.icon }} {{ g.label }}</span>
        </div>
      </div>
      <label>🔐 强制接入路径
        <select v-model="form.enforcement_mode" :disabled="viewOnly" class="input">
          <option value="gateway">Tier1 网关托管</option>
          <option value="sdk">Tier2 SDK 自接入</option>
          <option value="both">两者兼有</option>
        </select>
      </label>
    </div>

    <!-- ② 权限组合预设 -->
    <div class="section-title"><span class="sec-accent">②</span> 权限组合预设
      <span class="text-secondary">接口 + 主体 + 可申请范围 + 数据权限</span>
    </div>
    <div v-for="(p, pi) in form.presets" :key="p.id" class="card preset-block">
      <div class="preset-head">
        <span class="preset-idx">{{ pi + 1 }}</span>
        <b>预设 · {{ p.name || '（未命名）' }}</b>
        <span class="tag" :class="p.status === 'published' ? 'tag-ok' : 'tag-warn'">{{ p.status === 'published' ? '已上架' : '草稿' }}</span>
        <span class="mono text-secondary" style="margin-left:auto;">id: {{ p.id }}</span>
        <button v-if="!viewOnly" class="btn btn-sm" @click="removePreset(pi)">✕ 删除</button>
      </div>
      <div class="form-grid">
        <label>预设名称
          <input v-model="p.name" :disabled="viewOnly" class="input" />
        </label>
        <label>预设描述
          <input v-model="p.desc" :disabled="viewOnly" class="input" />
        </label>
      </div>

      <div class="sub-title">🔗 绑定接口 <span class="text-secondary">（点击分组展开选择）</span></div>
      <div v-for="g in treeGroups" :key="g.resource" class="collapsible" :class="{ open: openTree === g.resource }">
        <div class="c-head" @click="openTree = openTree === g.resource ? '' : g.resource">
          <span>{{ g.resource }}</span>
          <span class="c-meta">{{ g.ops.length }} 接口</span>
          <span class="c-chev">{{ openTree === g.resource ? '▾' : '▸' }}</span>
        </div>
        <div class="c-body">
          <label v-for="op in g.ops" :key="op.code" class="check">
            <input type="checkbox" :checked="p.action_codes.includes(op.code)"
              :disabled="viewOnly" @change="onActionChange(p, op.code, $event)" />
            <span class="method-tag" :class="op.operation">{{ op.operation }}</span>
            <span class="mono">{{ op.code }}</span>
          </label>
        </div>
      </div>

      <div class="sub-title">👤 权限可作用主体</div>
      <div class="chip-row">
        <span v-for="g in GRANTEE_OPTIONS" :key="g.v" class="chip" :class="{ on: p.grantee_types.includes(g.v) }"
          @click="!viewOnly && togglePresetGrantee(p, g.v)">{{ g.icon }} {{ g.label }}</span>
      </div>

      <div class="sub-title">🎯 可申请范围</div>
      <div class="scope-section">
        <label class="scope-label">组织级别
          <span class="scope-hint">（空 = 不限）</span>
        </label>
        <div class="chip-row">
          <span v-for="(o, oi) in p.apply_scope.orgs" :key="oi" class="chip chip-sel">
            {{ shortOrg(o) }}<span class="x" @click="!viewOnly && p.apply_scope.orgs.splice(oi, 1)">×</span>
          </span>
          <button v-if="!viewOnly" class="chip-add" @click="togglePicker(pi, 'org')">＋ 添加组织</button>
          <span v-if="!p.apply_scope.orgs?.length && viewOnly" class="text-tertiary">不限</span>
        </div>
        <div v-if="picker.pi === pi && picker.kind === 'org' && !viewOnly" class="picker-panel">
          <input v-model="picker.query" class="input input-sm" placeholder="搜索组织…" @keyup.enter="addFromPicker(p, 'org')" />
          <div class="picker-list">
            <div v-for="o in filteredOrgs" :key="o" class="picker-item" @click="pickOrg(p, o)">{{ o }}</div>
            <div v-if="!filteredOrgs.length" class="picker-empty">无匹配组织</div>
          </div>
        </div>
        <div v-if="p.apply_scope.orgs?.length && viewOnly" class="chip-row" style="margin-top:4px;">
          <span v-for="(o, oi) in p.apply_scope.orgs" :key="oi" class="chip chip-sel">{{ o }}</span>
        </div>
      </div>

      <div class="scope-section">
        <label class="scope-label">人员级别
          <span class="scope-hint">（选择特定的人，空 = 不限）</span>
        </label>
        <div class="chip-row">
          <span v-for="(u, ui) in p.apply_scope.people" :key="ui" class="chip chip-sel">
            {{ u }}<span class="x" @click="!viewOnly && p.apply_scope.people.splice(ui, 1)">×</span>
          </span>
          <button v-if="!viewOnly" class="chip-add" @click="togglePicker(pi, 'people')">＋ 添加人员</button>
          <span v-if="!p.apply_scope.people?.length && viewOnly" class="text-tertiary">不限</span>
        </div>
        <div v-if="picker.pi === pi && picker.kind === 'people' && !viewOnly" class="picker-panel">
          <input v-model="picker.query" class="input input-sm" placeholder="搜索人员…" @keyup.enter="addFromPicker(p, 'people')" />
          <div class="picker-list">
            <div v-for="u in filteredPeople" :key="u" class="picker-item" @click="pickPerson(p, u)">{{ u }}</div>
            <div v-if="!filteredPeople.length" class="picker-empty">无匹配人员</div>
          </div>
        </div>
        <div v-if="p.apply_scope.people?.length && viewOnly" class="chip-row" style="margin-top:4px;">
          <span v-for="(u, ui) in p.apply_scope.people" :key="ui" class="chip chip-sel">{{ u }}</span>
        </div>
      </div>

      <div class="scope-section scope-last">
        <label class="scope-label">自建组级别</label>
        <div class="switch-row">
          <label class="switch-label">
            <input type="checkbox" v-model="p.apply_scope.groups_free" :disabled="viewOnly" class="check-input" />
            <span>自建组不限制</span>
            <span class="field-hint-inline">（关闭后需指定可申请的自建组）</span>
          </label>
        </div>
      </div>

      <div class="sub-title">🗄️ 数据权限控制（每预设独立）</div>
      <label class="check switch-row">
        <input type="checkbox" v-model="p.data_control" :disabled="viewOnly" @change="onDataControlChange(p)" />
        <span>{{ p.data_control ? '开启：绑定接口 + 数据范围双重控制' : '关闭：绑定接口可访问全部数据' }}</span>
      </label>

      <template v-if="p.data_control">
        <div class="sub-title">数据模型（多选）</div>
        <div class="chip-row">
          <span v-for="mc in appModels" :key="mc" class="chip" :class="{ on: p.data_models.includes(mc) }"
            @click="!viewOnly && toggleModel(p, mc)">{{ mc }}</span>
        </div>

        <!-- T6 预设参数联动 + 层级编排（§4.2 升级一/二）：联动=申请时只选一次防域间错位；树=编排不是存储（落底各域仍独立策略） -->
        <div class="sub-title" style="margin-top:10px;">🔗 参数联动 <span class="text-secondary">（升级设计：场景参数一次选定，全域同值防错位）</span></div>
        <div class="form-grid">
          <label>联动模式
            <select v-model="p.param_linkage" :disabled="viewOnly" class="input">
              <option value="independent">独立（各域各选——现状）</option>
              <option value="shared">联动（共享场景参数——全域同值）</option>
            </select>
          </label>
        </div>
        <template v-if="p.param_linkage === 'shared'">
          <div class="text-secondary" style="font-size:12px;margin:4px 0 6px;">场景参数（申请时只选一次；各域条件字段与参数 key 同名 → 值锁定为 <span class="mono">$key</span> 引用）：</div>
          <div v-for="(sp, spi) in p.scenario_params || []" :key="spi" class="chip-row" style="margin-bottom:6px;">
            <input v-model="sp.key" :disabled="viewOnly" class="input input-sm" placeholder="key（如 account）" style="width:130px;" />
            <input v-model="sp.label" :disabled="viewOnly" class="input input-sm" placeholder="显示名" style="width:120px;" />
            <select v-model="sp.type" :disabled="viewOnly" class="input input-sm" style="width:100px;">
              <option value="select">select</option>
              <option value="input">input</option>
            </select>
            <input v-if="sp.type === 'select'" v-model="sp._choices" :disabled="viewOnly" class="input input-sm" placeholder="选项：显示名=值,…" style="width:240px;" />
            <label class="m-check" style="white-space:nowrap;"><input type="checkbox" v-model="sp.required" :disabled="viewOnly" /> 必填</label>
            <button v-if="!viewOnly" class="btn btn-sm" @click="(p.scenario_params || []).splice(spi, 1)">✕</button>
          </div>
          <button v-if="!viewOnly" class="btn btn-sm" @click="addScenarioParam(p)">＋ 场景参数</button>
        </template>

        <template v-if="p.data_control && (p.data_models || []).length > 1">
          <div class="sub-title" style="margin-top:10px;">🌲 层级编排 <span class="text-secondary">（子域随父域带出；落底层各域仍是独立策略——层级是编排不是存储）</span></div>
          <div v-for="mc in p.data_models" :key="'tp' + mc" class="chip-row" style="margin-bottom:4px;">
            <span class="chip on mono">{{ mc }}</span>
            <span class="text-secondary" style="font-size:12px;">← 父域：</span>
            <select :value="treeParentOf(p, mc)" :disabled="viewOnly" class="input input-sm" style="width:150px;" @change="setTreeParent(p, mc, ($event.target as HTMLSelectElement).value)">
              <option value="">（顶层——独立申请）</option>
              <option v-for="pm in (p.data_models || []).filter((m: string) => m !== mc)" :key="pm" :value="pm">{{ pm }}</option>
            </select>
          </div>
          <div class="text-secondary" style="font-size:11px;">跨出层级（管其他账号的磁盘）→ 不挂树 → 申请时单独选值。</div>
        </template>

        <div v-for="mc in p.data_models" :key="mc" class="dim-block">
          <div class="dim-head"><b class="mono">{{ mc }}</b>
            <span class="tag tag-info">范围选项（owner 配置 applicant 可选类型）</span>
          </div>
          <div class="scope-list">
            <div v-for="(o, oi) in scopeOptionsOf(p, mc)" :key="oi" class="scope-opt">
              <div class="scope-opt-head">
                <span class="so-icon">{{ SCOPE_ICON[o.type] }}</span>
                <span class="tag">{{ SCOPE_LABEL[o.type] || o.type }}</span>
                <input v-model="o.label" :disabled="viewOnly" class="input input-sm" placeholder="显示名" style="width:160px;" />
                <span v-if="o.desc" class="text-secondary so-desc">{{ o.desc }}</span>
                <button v-if="!viewOnly" class="btn btn-sm" style="margin-left:auto;" @click="removeScopeOpt(p, mc, oi)">✕</button>
              </div>
              <div v-if="['select','multi_select','variable','input'].includes(o.type)" class="scope-opt-body">
                <select v-model="o.field" :disabled="viewOnly" class="input input-sm" style="width:140px;">
                  <option value="">字段…</option>
                  <option v-for="f in fieldsOf(mc)" :key="f.name" :value="f.name">{{ f.name }}</option>
                </select>
                <select v-model="o.op" :disabled="viewOnly" class="input input-sm" style="width:90px;">
                  <option v-for="op in SCOPE_OPS[o.type]" :key="op" :value="op">{{ op }}</option>
                </select>
                <template v-if="o.type === 'select' || o.type === 'multi_select'">
                  <span class="text-secondary" style="font-size:11px;">→ 选项列表：</span>
                  <div class="chip-row">
                    <span v-for="(ch, ci) in o.choices" :key="ci" class="chip choice-chip">
                      {{ ch.label }}<span class="mono"> {{ ch.value }}</span>
                      <span class="x" @click="!viewOnly && o.choices.splice(ci, 1)">×</span>
                    </span>
                  </div>
                  <div v-if="!viewOnly" class="choice-add">
                    <input v-model="choiceDraft.label[`${p.id}_${mc}_${oi}`]" class="input input-sm" placeholder="显示名" />
                    <input v-model="choiceDraft.value[`${p.id}_${mc}_${oi}`]" class="input input-sm" placeholder="值(value)" />
                    <button class="btn btn-sm" @click="addChoice(p, mc, oi)">＋ 添加</button>
                  </div>
                </template>
                <template v-if="o.type === 'variable'">
                  <select v-model="o.variable" :disabled="viewOnly" class="input input-sm" style="flex:1;">
                    <option v-for="v in VARIABLES" :key="v.v" :value="v.v">{{ v.v }}（{{ v.label }}）</option>
                  </select>
                </template>
                <template v-if="o.type === 'input'">
                  <input v-model="o.placeholder" :disabled="viewOnly" class="input input-sm" style="flex:1;" placeholder="placeholder 提示" />
                </template>
              </div>
              <div v-else class="text-secondary so-desc">{{ o.desc || '—' }}</div>
            </div>
          </div>
          <div v-if="!viewOnly" class="add-opts">
            <button v-for="t in ['select','multi_select','variable','input']" :key="t" class="btn btn-sm"
              @click="addScopeOpt(p, mc, t)">＋ {{ SCOPE_LABEL[t] }}</button>
          </div>
        </div>
      </template>

      <!-- 数据契约（清单 A2 发布必填：字段 + 算法档位 + 新鲜度承诺；
           发布时后端另有失败二分自检：字段不可算=400 拒绝+出路；端点不可达=502 可重试非拒绝） -->
      <template v-if="p.data_control && p.data_contract">
        <div class="sub-title">📜 数据契约 <span class="text-secondary">（勾选数据级 → 发布必填）</span></div>
        <p class="field-hint">字段须能算出确定性指纹（三元素：新增/删除/更新可判定）——算不出的出路：不勾数据级、只发接口级能力包。发布时自动做指纹端点可达自检（不可达=可重试提示，不算契约拒绝）。</p>
        <div class="form-grid">
          <label class="span2">指纹字段
            <div class="chip-row">
              <span v-for="f in contractFieldOptions(p)" :key="f" class="chip" :class="{ on: p.data_contract.fields.includes(f) }"
                @click="!viewOnly && toggleContractField(p, f)">{{ f }}</span>
            </div>
          </label>
          <label>算法档位
            <select v-model="p.data_contract.algorithm" :disabled="viewOnly" class="input">
              <option value="L1">L1 · count + max(updated_at)（最简）</option>
              <option value="L2">L2 · 集合哈希（推荐）</option>
              <option value="L3">L3 · 判定字段全量哈希（最强）</option>
            </select>
          </label>
          <label>新鲜度承诺 SLA（秒）
            <input type="number" v-model.number="p.data_contract.staleness_sla_sec" :disabled="viewOnly" class="input" min="1" />
          </label>
          <label>降级容忍上限（秒，0 = SLA×6）
            <input type="number" v-model.number="p.data_contract.degrade_max_age_sec" :disabled="viewOnly" class="input" min="0" />
          </label>
        </div>
      </template>
    </div>
    <button v-if="!viewOnly" class="btn preset-add" @click="addPreset">＋ 添加预设</button>

    <!-- ③ 声明文件 -->
    <div class="section-title"><span class="sec-accent">③</span> 声明文件</div>
    <div class="card">
      <div class="view-tabs">
        <button class="btn btn-sm" :class="{ on: docView === 'form' }" @click="docView = 'form'">📝 表单</button>
        <button class="btn btn-sm" :class="{ on: docView === 'yaml' }" @click="docView = 'yaml'">YAML</button>
        <button class="btn btn-sm" :class="{ on: docView === 'json' }" @click="docView = 'json'">JSON</button>
      </div>
      <div v-if="docView === 'yaml'" class="doc-box">
        <textarea v-model="yamlEdit" :disabled="viewOnly" rows="22" class="input mono-input" spellcheck="false"></textarea>
        <button v-if="!viewOnly" class="btn btn-sm" @click="applyYaml">从 YAML 应用到表单</button>
      </div>
      <pre v-else-if="docView === 'json'" class="codeblock">{{ jsonText }}</pre>
      <div v-else class="text-secondary" style="padding:8px 0;">当前为表单视图，编辑上方表单后保存即可；切到 YAML/JSON 可查看规范声明。</div>
    </div>

    <div v-if="!viewOnly" class="save-bar">
      <span v-if="saveMsg" class="save-msg" :class="{ err: saveErr }">{{ saveMsg }}</span>
      <button class="btn btn-primary" @click="save" :disabled="saving">{{ saving ? '保存中…' : '💾 保存' }}</button>
    </div>
  </div>
  <div v-else class="empty-state" style="padding:60px;">加载中…</div>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import { api } from '../api/client'
import { dump as yamlDump, load as yamlLoad } from 'js-yaml'

const route = useRoute()
const appId = Number(route.params.id)
const cid = Number(route.params.cid)
const viewOnly = computed(() => route.query.view === '1' || route.query.view === 'true')

const ALL_TAGS = ['主机', '数据库', '工单', '云', '财务', '只读']
const GRANTEE_OPTIONS = [
  { v: 'user', icon: '👤', label: '用户' },
  { v: 'org', icon: '🏢', label: '组织' },
  { v: 'group', icon: '👥', label: '自建组' },
  { v: 'app', icon: '🔌', label: '程序' },
]
const SCOPE_LABEL: Record<string, string> = { all: '所有数据', instance: '具体实例', select: '单选', multi_select: '多选', variable: '自动匹配', input: '自由输入' }
const SCOPE_ICON: Record<string, string> = { all: '🌍', instance: '📌', select: '📋', multi_select: '☑️', variable: '🔄', input: '⌨️' }
const SCOPE_OPS: Record<string, string[]> = {
  select: ['==', '!=', 'in', '!in'],
  multi_select: ['in', '!in'], // D6：仅这两项
  variable: ['==', '!='],
  input: ['==', '!=', 'contains', 'startsWith', 'in'],
}
const VARIABLES = [
  { v: '@currentUser', label: '当前用户' },
  { v: '@currentOrg', label: '当前组织' },
  { v: '@currentGroup', label: '当前自建组' },
  { v: '@currentAccount', label: '当前账号' },
]

const app = ref<any>(null)
const cap = ref<any>(null)
const actions = ref<any[]>([])
const allResourceModels = ref<any[]>([])
const saving = ref(false)
const saveMsg = ref('')
const saveErr = ref(false)
const docView = ref<'form' | 'yaml' | 'json'>('form')
const yamlEdit = ref('')
const openTree = ref('')
const choiceDraft = reactive<{ label: Record<string, string>; value: Record<string, string> }>({ label: {}, value: {} })
const newOrg = reactive<Record<number, string>>({})
const picker = reactive({ pi: -1, kind: '', query: '' })

const ALL_ORGS = [
  '总公司 → 研发中心 → 研发一部',
  '总公司 → 研发中心 → 研发二部',
  '总公司 → 运维中心 → 平台运维部',
  '总公司 → 运维中心 → 应用运维部',
]
const ALL_PEOPLE = ['alice', 'bob', 'erin', 'frank']

const form = reactive<{
  name: string
  description: string
  visibility: string
  grantee_types: string[]
  enforcement_mode: string
  tags: string[]
  presets: any[]
}>({
  name: '',
  description: '',
  visibility: 'public',
  grantee_types: [],
  enforcement_mode: 'gateway',
  tags: [],
  presets: [],
})

const appModels = computed(() => {
  // 从 API 获取的所有资源模型中提取数据模型名称
  const set = new Set<string>()
  for (const m of allResourceModels.value) {
    if (m.code) set.add(m.code)
  }
  // 如果 API 没有返回模型，回退到预设中已选的并集
  if (set.size === 0) {
    for (const p of form.presets) for (const mc of p.data_models || []) set.add(mc)
  }
  return [...set]
})

const treeGroups = computed(() => {
  const m = new Map<string, any[]>()
  for (const a of actions.value) {
    if (!m.has(a.resource)) m.set(a.resource, [])
    m.get(a.resource)!.push(a)
  }
  return [...m.entries()].map(([resource, ops]) => ({ resource, ops }))
})

function fieldsOf(mc: string) {
  if (!app.value?.app?.model_fields && !cap.value?.model_fields) return []
  return (cap.value?.model_fields || app.value?.app?.model_fields || []).filter((f: any) =>
    !mc || mc === (cap.value?.data_model || ''))
}

function scopeOptionsOf(p: any, mc: string) {
  return p.scopeOptions?.[mc] || []
}

function shortOrg(o: string) {
  return o.split(' → ').pop() || o
}

const filteredOrgs = computed(() => {
  const q = picker.query.toLowerCase()
  const taken = new Set<string>()
  if (picker.pi >= 0 && form.presets[picker.pi]) {
    for (const o of form.presets[picker.pi].apply_scope.orgs || []) taken.add(o)
  }
  return ALL_ORGS.filter(o => !taken.has(o) && (!q || o.toLowerCase().includes(q)))
})

const filteredPeople = computed(() => {
  const q = picker.query.toLowerCase()
  const taken = new Set<string>()
  if (picker.pi >= 0 && form.presets[picker.pi]) {
    for (const u of form.presets[picker.pi].apply_scope.people || []) taken.add(u)
  }
  return ALL_PEOPLE.filter(u => !taken.has(u) && (!q || u.toLowerCase().includes(q)))
})

function togglePicker(pi: number, kind: string) {
  if (picker.pi === pi && picker.kind === kind) {
    picker.pi = -1; picker.kind = ''; picker.query = ''
  } else {
    picker.pi = pi; picker.kind = kind; picker.query = ''
  }
}
function pickOrg(p: any, org: string) {
  if (!p.apply_scope.orgs.includes(org)) p.apply_scope.orgs.push(org)
  picker.query = ''
}
function pickPerson(p: any, person: string) {
  if (!p.apply_scope.people.includes(person)) p.apply_scope.people.push(person)
  picker.query = ''
}
function addFromPicker(p: any, kind: string) {
  if (kind === 'org' && filteredOrgs.value.length) pickOrg(p, filteredOrgs.value[0])
  if (kind === 'people' && filteredPeople.value.length) pickPerson(p, filteredPeople.value[0])
  picker.query = ''
}
// ---- 数据契约（清单 A2：发布必填，UI 闭环）----
function defaultContract() {
  return { fields: ['name', 'owner_id'], algorithm: 'L2', staleness_sla_sec: 300, degrade_max_age_sec: 0 }
}
// ensureContract：data_control 开启的预设必须持有契约对象（load/YAML 应用/开关三入口自愈填充默认）
function ensureContract(p: any) {
  if (p.data_control && !p.data_contract) p.data_contract = defaultContract()
}
function onDataControlChange(p: any) { ensureContract(p) }
// 字段白名单 = 能力包资源模型字段 ∪ 基础判定字段（与后端 validateDataContractSpec 同一集合）
function contractFieldOptions(p: any) {
  const base = ['name', 'owner_id', 'external_id', 'updated_at']
  const names = (fieldsOf(p.data_models?.[0]) || []).map((f: any) => f.name).filter(Boolean)
  return [...new Set([...names, ...base])]
}
function toggleContractField(p: any, f: string) {
  ensureContract(p)
  const arr = p.data_contract.fields as string[]
  const i = arr.indexOf(f)
  i < 0 ? arr.push(f) : arr.splice(i, 1)
}

function toggleTag(t: string) {
  const i = form.tags.indexOf(t)
  i >= 0 ? form.tags.splice(i, 1) : form.tags.push(t)
}
function toggleGrantee(g: string) {
  const i = form.grantee_types.indexOf(g)
  i >= 0 ? form.grantee_types.splice(i, 1) : form.grantee_types.push(g)
}
function togglePresetGrantee(p: any, g: string) {
  if (!p.grantee_types) p.grantee_types = []
  const i = p.grantee_types.indexOf(g)
  i >= 0 ? p.grantee_types.splice(i, 1) : p.grantee_types.push(g)
}
function toggleAction(p: any, code: string, on: boolean) {
  if (!p.action_codes) p.action_codes = []
  const i = p.action_codes.indexOf(code)
  on && i < 0 ? p.action_codes.push(code) : !on && i >= 0 ? p.action_codes.splice(i, 1) : 0
}
function onActionChange(p: any, code: string, e: Event) {
  toggleAction(p, code, (e.target as HTMLInputElement).checked)
}
function toggleModel(p: any, mc: string) {
  if (!p.data_models) p.data_models = []
  const i = p.data_models.indexOf(mc)
  if (i < 0) p.data_models.push(mc)
  else p.data_models.splice(i, 1)
}
function addPreset() {
  form.presets.push({
    id: 'p' + Date.now().toString(36),
    name: '新预设',
    status: 'draft',
    desc: '',
    action_codes: [],
    grantee_types: ['user'],
    apply_scope: { orgs: [], people: [], groups_free: true },
    data_control: false,
    data_models: [],
    scopeOptions: {},
    // T6：参数联动 + 层级编排（可选字段，缺省=独立+平面向后兼容）
    param_linkage: 'independent',
    scenario_params: [],
  })
}
// T6 场景参数（§4.2 升级一）：key/label/type/choices(_choices 编辑态 "显示名=值,…")
function addScenarioParam(p: any) {
  if (!p.scenario_params) p.scenario_params = []
  p.scenario_params.push({ key: '', label: '', type: 'select', required: true, _choices: '' })
}
// T6 层级编排（§4.2 升级二）：编辑态用平铺 parent 映射（data_model_tree 存树——编排不是存储）
function treeParentOf(p: any, mc: string): string {
  const walk = (nodes: any[], parent: string): string => {
    for (const n of nodes || []) {
      if (n?.model === mc) return parent
      const hit = walk(n?.children || [], n?.model)
      if (hit) return hit
    }
    return ''
  }
  return walk(p.data_model_tree || [], '')
}
function setTreeParent(p: any, mc: string, parent: string) {
  // 重建树：先收集现有父子映射，改动一条，重建嵌套结构（防环——子不能做父的祖先）
  const parents: Record<string, string> = {}
  for (const m of p.data_models || []) parents[m] = treeParentOf(p, m)
  parents[mc] = parent
  if (parent) { // 防环：沿新父链上溯，若遇到 mc 说明成环 → 拒绝（落回空）
    let cur = parent, guard = 0
    while (cur && guard < 10) { if (cur === mc) { parents[mc] = ''; break } cur = parents[cur] || ''; guard++ }
  }
  const roots: any[] = []
  const nodeOf: Record<string, any> = {}
  for (const m of p.data_models || []) { nodeOf[m] = { model: m, children: [] } }
  for (const m of p.data_models || []) {
    const par = parents[m]
    if (par && nodeOf[par]) nodeOf[par].children.push(nodeOf[m])
    else roots.push(nodeOf[m])
  }
  const prune = (nodes: any[]) => { for (const n of nodes) { n.children = prune(n.children || []) } return nodes.filter((n: any) => n.model) }
  p.data_model_tree = prune(roots)
}
// scenario_params choices 编辑态解析："显示名=值,显示名2=值2" → [{label,value}]
function scenarioParamsForSave(p: any) {
  return (p.scenario_params || []).map((sp: any) => {
    const out: any = { key: (sp.key || '').trim(), label: (sp.label || sp.key || '').trim(), type: sp.type || 'select', required: sp.required !== false }
    if (sp.type === 'select') {
      out.choices = String(sp._choices || '').split(',').map((pair: string) => {
        const [label, value] = pair.split('=').map((s: string) => s.trim())
        return { label: label || value, value: value || label }
      }).filter((c: any) => c.value)
    }
    return out
  }).filter((sp: any) => sp.key)
}
function removePreset(pi: number) {
  form.presets.splice(pi, 1)
}
function addScopeOpt(p: any, mc: string, type: string) {
  if (!p.scopeOptions) p.scopeOptions = {}
  if (!p.scopeOptions[mc]) p.scopeOptions[mc] = []
  const o: any = { type, label: SCOPE_LABEL[type], desc: '', choices: [] }
  if (type === 'select' || type === 'multi_select') { o.field = ''; o.op = type === 'multi_select' ? 'in' : '=='; o.choices = [] }
  if (type === 'variable') { o.field = ''; o.op = '=='; o.variable = '@currentUser'; o.var_label = '当前用户' }
  if (type === 'input') { o.field = ''; o.op = 'contains'; o.placeholder = '' }
  p.scopeOptions[mc].push(o)
}
function removeScopeOpt(p: any, mc: string, oi: number) {
  if (p.scopeOptions?.[mc]) p.scopeOptions[mc].splice(oi, 1)
}
function addChoice(p: any, mc: string, oi: number) {
  const o = p.scopeOptions?.[mc]?.[oi]
  if (!o) return
  const k = `${p.id}_${mc}_${oi}`
  const label = (choiceDraft.label[k] || '').trim()
  const value = (choiceDraft.value[k] || '').trim()
  if (label && value) {
    o.choices.push({ label, value })
    choiceDraft.label[k] = ''
    choiceDraft.value[k] = ''
  }
}

function manifestForYaml() {
  return {
    capability: {
      name: form.name,
      app_name: app.value?.app?.name,
      enforcement_mode: form.enforcement_mode,
      visibility: { type: form.visibility },
      grantee_types: form.grantee_types,
      tags: form.tags,
      presets: form.presets.map((p: any) => ({
        id: p.id,
        name: p.name,
        status: p.status,
        desc: p.desc,
        action_codes: p.action_codes,
        grantee_types: p.grantee_types,
        apply_scope: p.apply_scope,
        data_control: p.data_control,
        data_models: p.data_models,
        data_contract: p.data_contract,
      })),
    },
  }
}

const yamlText = computed(() => yamlDump(manifestForYaml(), { noRefs: true, lineWidth: 120 }))
const jsonText = computed(() => JSON.stringify(manifestForYaml().capability, null, 2))

watch(docView, (v) => {
  if (v === 'yaml') yamlEdit.value = yamlText.value
})

function applyYaml() {
  try {
    const doc = yamlLoad(yamlEdit.value) as any
    const c = doc?.capability || doc
    if (!c || !Array.isArray(c.presets)) throw new Error('YAML 缺少 capability.presets')
    form.name = c.name ?? form.name
    form.description = c.description ?? form.description
    form.visibility = c.visibility?.type ?? form.visibility
    form.grantee_types = c.grantee_types ?? form.grantee_types
    form.enforcement_mode = c.enforcement_mode ?? form.enforcement_mode
    form.tags = c.tags ?? form.tags
    form.presets = c.presets.map((p: any) => ({
      ...p,
      apply_scope: p.apply_scope || { orgs: [], people: [], groups_free: true },
      data_models: p.data_models || [],
      action_codes: p.action_codes || [],
      grantee_types: p.grantee_types || [],
      scopeOptions: {},
    }))
    for (const p of form.presets) ensureContract(p)
    saveMsg.value = '已从 YAML 应用到表单'
    saveErr.value = false
  } catch (e: any) {
    saveMsg.value = 'YAML 解析失败：' + e.message
    saveErr.value = true
  }
}

async function load() {
  const detail = await api.appDetail(appId)
  app.value = detail
  const caps = await api.capabilities(appId)
  cap.value = caps.items.find((c: any) => c.id === cid)
  actions.value = (await api.actions(appId)).items || []
  // 获取所有资源模型（用于数据模型多选）
  try {
    const rm = await api.resourceModels()
    allResourceModels.value = (rm as any).items || rm || []
  } catch { allResourceModels.value = [] }
  if (!cap.value) return
  form.name = cap.value.name
  form.description = cap.value.description || ''
  form.visibility = cap.value.visibility || 'public'
  form.grantee_types = cap.value.grantee_types || ['user', 'org', 'group', 'app']
  form.enforcement_mode = cap.value.enforcement_mode || 'gateway'
  form.tags = cap.value.tags || []
  form.presets = (cap.value.presets || []).map((p: any) => ({
    ...p,
    apply_scope: p.apply_scope || { orgs: [], people: [], groups_free: true },
    data_models: p.data_models || [],
    action_codes: p.action_codes || [],
    grantee_types: p.grantee_types || [],
    // T6：联动/层级字段回填 + scenario_params 编辑态（choices 数组 → _choices 串）
    param_linkage: p.param_linkage || 'independent',
    scenario_params: (p.scenario_params || []).map((sp: any) => ({ ...sp, _choices: (sp.choices || []).map((c: any) => `${c.label}=${c.value}`).join(',') })),
    scopeOptions: {},
  }))
  // 加载各预设×模型的范围选项（独立表）
  for (const p of form.presets) {
    ensureContract(p) // A2：已开数据级但缺契约的旧预设 → 回填默认（发布门禁可正向通过）
    p.scopeOptions = {}
    for (const mc of p.data_models || []) {
      try {
        const r = await api.presetScopeOptions(cid, p.id, mc)
        p.scopeOptions[mc] = (r.options || []).map((o: any) => ({ ...o, choices: o.choices || [] }))
      } catch {
        p.scopeOptions[mc] = []
      }
    }
  }
  if (docView.value === 'yaml') yamlEdit.value = yamlText.value
  if (viewOnly.value) docView.value = 'yaml'
}

async function save() {
  saving.value = true
  saveMsg.value = ''
  saveErr.value = false
  try {
    // 1. 校验 + 保存范围选项（独立表）
    for (const p of form.presets) {
      for (const mc of p.data_models || []) {
        const opts = p.scopeOptions?.[mc] || []
        await api.validateScopeOptions(cid, p.id, mc, opts)
        if (opts.length) await api.savePresetScopeOptions(cid, p.id, mc, opts)
      }
    }
    // 2. 保存能力主体（presets JSON 不含 scopeOptions）
    const payload = {
      name: form.name,
      description: form.description,
      visibility: form.visibility,
      grantee_types: form.grantee_types,
      enforcement_mode: form.enforcement_mode,
      tags: form.tags,
      presets: form.presets.map((p: any) => ({
        id: p.id, name: p.name, status: p.status, desc: p.desc,
        action_codes: p.action_codes, grantee_types: p.grantee_types,
        apply_scope: p.apply_scope, data_control: p.data_control, data_models: p.data_models,
        data_contract: p.data_contract, // A2：数据契约随预设透传（发布门禁校验对象）
        // T6（§4.2）：参数联动 + 层级编排（缺省 independent/空树=向后兼容）
        param_linkage: p.param_linkage || 'independent',
        scenario_params: scenarioParamsForSave(p),
        data_model_tree: (p.data_model_tree || []).length ? p.data_model_tree : undefined,
      })),
    }
    await api.updateCapability(appId, cid, payload)
    saveMsg.value = '✅ 已保存'
    await load()
  } catch (e: any) {
    saveMsg.value = '保存失败：' + e.message
    saveErr.value = true
  } finally {
    saving.value = false
  }
}

onMounted(load)
</script>

<style scoped>
.cap-editor { max-width: 980px; }
.page-header { margin-bottom: 20px; }
.page-header h1 { font-size: 22px; font-weight: 700; display: flex; align-items: center; gap: 10px; }
.back-link { font-size: 13px; color: var(--accent); text-decoration: none; display: inline-block; margin-bottom: 6px; }
.back-link:hover { text-decoration: underline; }
.page-desc { font-size: 13px; color: var(--text-secondary); }

/* Section titles */
.section-title { font-size: 15px; font-weight: 700; margin: 24px 0 12px; display: flex; align-items: center; gap: 10px; }
.section-title .text-secondary { font-size: 12px; font-weight: 400; }
.sec-accent { display: inline-flex; align-items: center; justify-content: center; width: 22px; height: 22px; border-radius: 6px; background: var(--accent); color: var(--accent-text); font-size: 11px; font-weight: 700; }

/* Card (replaces panel) */
.card { border: 1px solid var(--border); background: var(--bg-card); padding: 20px; margin-bottom: 14px; border-radius: var(--radius, 10px); box-shadow: var(--shadow-sm); }

/* Grid form */
.form-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 14px 20px; }
.form-grid > label, .form-grid > .field-full { font-size: 13px; font-weight: 600; display: flex; flex-direction: column; gap: 5px; }
.form-grid .span2 { grid-column: span 2; }
.field-full { grid-column: span 2; }
.field-hint { font-size: 11px; font-weight: 400; color: var(--text-tertiary); margin: -2px 0 4px; }

/* App badge */
.app-badge { display: inline-flex; align-items: center; gap: 6px; padding: 4px 12px; background: var(--accent-soft, var(--brand-soft, #eaf1fe)); color: var(--accent, var(--brand, #2f6fed)); border-radius: 6px; font-size: 13px; font-weight: 600; }
.app-code { font-family: var(--font-mono); font-size: 11px; opacity: .7; }

/* Inputs */
.input { width: 100%; padding: 9px 12px; border: 1px solid var(--border); border-radius: 8px; background: var(--bg-card); color: var(--text); font-size: 13px; transition: all .15s; }
.input:focus { outline: none; border-color: var(--accent, var(--brand, #2f6fed)); box-shadow: 0 0 0 3px rgba(47,111,237,.12); }
.input:disabled { background: var(--bg-secondary); color: var(--text-secondary); }
.input-sm { width: auto; padding: 6px 10px; font-size: 12px; }
.mono-input { font-family: var(--font-mono); font-size: 12px; line-height: 1.6; }

/* Buttons - consistent with v12 demo */
.btn { padding: 9px 18px; font-size: 13px; font-weight: 600; border: none; border-radius: 8px; cursor: pointer; transition: all .15s; display: inline-flex; align-items: center; gap: 6px; }
.btn-primary { background: var(--accent, var(--brand, #2f6fed)); color: var(--accent-text, #fff); }
.btn-primary:hover { background: var(--accent-hover, var(--brand-strong, #1e5ad7)); }
.btn-primary:disabled { opacity: .5; cursor: not-allowed; }
.btn-secondary { background: var(--bg-card); color: var(--text-secondary); border: 1px solid var(--border); }
.btn-secondary:hover { background: var(--bg-hover); color: var(--text); border-color: var(--border-strong); }
.btn-ghost { background: transparent; color: var(--text-secondary); border: 1px solid var(--border); }
.btn-ghost:hover { background: var(--bg-hover); color: var(--text); border-color: var(--border-strong); }
.btn-danger { background: var(--danger, #dc2626); color: #fff; }
.btn-danger:hover { background: #b91c1c; }
.btn-sm { padding: 5px 12px; font-size: 12px; border-radius: 6px; }
.btn-icon { padding: 4px 8px; font-size: 11px; }

/* Chips */
.chip-row { display: flex; flex-wrap: wrap; gap: 6px; align-items: center; }
.chip { display: inline-flex; align-items: center; gap: 5px; padding: 4px 10px; border: 1px solid var(--border); border-radius: 999px; font-size: 12px; cursor: pointer; color: var(--text-secondary); transition: all .15s; }
.chip:hover { border-color: var(--border-strong); }
.chip.on { background: var(--accent, var(--brand, #2f6fed)); color: var(--accent-text, #fff); border-color: var(--accent, var(--brand, #2f6fed)); }
.chip .x { cursor: pointer; font-weight: 700; opacity: .6; }
.chip .x:hover { opacity: 1; }

/* Preset block */
.preset-block { border: 1px solid var(--border); border-radius: 12px; padding: 16px; margin-bottom: 12px; background: var(--bg-card); box-shadow: var(--shadow-sm); }
.preset-head { display: flex; align-items: center; gap: 10px; margin-bottom: 14px; padding-bottom: 12px; border-bottom: 1px solid var(--border); }
.preset-idx { width: 26px; height: 26px; border-radius: 8px; background: var(--accent, var(--brand, #2f6fed)); color: var(--accent-text, #fff); display: inline-flex; align-items: center; justify-content: center; font-size: 12px; font-weight: 700; flex-shrink: 0; }

/* Sub titles */
.sub-title { font-size: 12px; font-weight: 700; margin: 16px 0 8px; color: var(--text-secondary); display: flex; align-items: center; gap: 6px; }
.sub-title::after { content: ''; flex: 1; height: 1px; background: var(--border); }

/* Info hints */
.info-hint { font-size: 11px; color: var(--text-tertiary); background: var(--bg-secondary); border: 1px solid var(--border); border-radius: 6px; padding: 6px 10px; margin-bottom: 10px; }
.field-hint-inline { font-size: 11px; font-weight: 400; color: var(--text-tertiary); }

/* Scope labels */
.scope-section { margin-bottom: 12px; padding-bottom: 12px; border-bottom: 1px solid var(--border); }
.scope-section.scope-last { border-bottom: none; margin-bottom: 0; padding-bottom: 0; }
.scope-label { font-size: 13px; font-weight: 600; display: inline-flex; align-items: center; gap: 6px; margin-bottom: 6px; }
.scope-hint { font-size: 11px; font-weight: 400; color: var(--text-tertiary); }
.chip-sel { background: var(--accent-soft, var(--brand-soft, #eaf1fe)); color: var(--accent, var(--brand, #2f6fed)); border-color: var(--accent, var(--brand, #2f6fed)); }
.chip-add { display: inline-flex; align-items: center; gap: 4px; padding: 5px 12px; border: 1px dashed var(--border-strong); border-radius: 999px; font-size: 12px; font-weight: 500; cursor: pointer; color: var(--accent, var(--brand, #2f6fed)); background: transparent; transition: all .15s; }
.chip-add:hover { border-color: var(--accent, var(--brand, #2f6fed)); background: var(--accent-soft, var(--brand-soft, #eaf1fe)); }
.picker-panel { border: 1px solid var(--border); border-radius: 10px; padding: 10px; margin-top: 8px; background: var(--bg-card); box-shadow: var(--shadow-md); }
.picker-list { max-height: 180px; overflow-y: auto; margin-top: 8px; }
.picker-item { padding: 8px 12px; font-size: 12px; cursor: pointer; border-radius: 8px; transition: background .1s; }
.picker-item:hover { background: var(--bg-hover); color: var(--accent, var(--brand, #2f6fed)); }
.picker-empty { padding: 12px; font-size: 11px; color: var(--text-tertiary); text-align: center; }
.switch-label { display: inline-flex; align-items: center; gap: 6px; font-size: 13px; font-weight: 600; cursor: pointer; }
.check-input { accent-color: var(--accent); width: 16px; height: 16px; }
.text-tertiary { color: var(--text-tertiary); font-size: 12px; }

/* Collapsible */
.collapsible { border: 1px solid var(--border); margin-bottom: 8px; border-radius: 10px; overflow: hidden; background: var(--bg-card); }
.collapsible .c-head { display: flex; align-items: center; gap: 8px; padding: 10px 14px; cursor: pointer; font-size: 13px; font-weight: 600; transition: background .15s; }
.collapsible .c-head:hover { background: var(--bg-hover); }
.collapsible .c-meta { font-size: 11px; color: var(--text-tertiary); }
.collapsible .c-chev { margin-left: auto; color: var(--text-tertiary); font-size: 11px; transition: transform .15s; }
.collapsible.open .c-chev { transform: rotate(90deg); }
.collapsible .c-body { display: none; padding: 10px 14px; border-top: 1px solid var(--border); background: var(--bg-inset, var(--bg-secondary)); }
.collapsible.open .c-body { display: flex; flex-wrap: wrap; gap: 10px; }

/* Check / Switch */
.check { display: inline-flex; align-items: center; gap: 6px; font-size: 12px; cursor: pointer; padding: 4px 0; }
.switch-row { margin: 4px 0; }
.method-tag { padding: 2px 8px; border: 1px solid var(--border); font-size: 10px; text-transform: uppercase; letter-spacing: .3px; border-radius: 4px; font-weight: 600; }

/* Data model blocks */
.dim-block { border: 1px solid var(--border); border-radius: 10px; padding: 14px; margin-top: 10px; background: var(--bg-card); box-shadow: var(--shadow-sm); }
.dim-head { display: flex; align-items: center; gap: 10px; margin-bottom: 10px; }
.scope-list { display: flex; flex-direction: column; gap: 8px; }
.scope-opt { border: 1px solid var(--border); border-radius: 10px; padding: 12px 14px; background: var(--bg-card); }
.scope-opt-head { display: flex; align-items: center; gap: 8px; flex-wrap: wrap; }
.scope-opt-body { display: flex; gap: 8px; align-items: center; flex-wrap: wrap; margin-top: 8px; }
.so-icon { font-size: 16px; }
.so-desc { font-size: 11px; }
.choice-chip { cursor: default; }
.choice-add { display: flex; gap: 6px; flex: 1; min-width: 220px; }
.add-opts { display: flex; gap: 6px; margin-top: 8px; flex-wrap: wrap; }
.preset-add { width: 100%; border: 2px dashed var(--border-strong); border-radius: 12px; padding: 16px; text-align: center; color: var(--text-tertiary); font-size: 13px; font-weight: 600; cursor: pointer; transition: all .15s; background: transparent; margin-top: 8px; }
.preset-add:hover { border-color: var(--accent, var(--brand, #2f6fed)); color: var(--accent, var(--brand, #2f6fed)); background: var(--accent-soft, var(--brand-soft, #eaf1fe)); }

/* View tabs */
.view-tabs { display: flex; gap: 6px; margin-bottom: 10px; }
.view-tabs .btn.on { background: var(--accent, var(--brand, #2f6fed)); color: var(--accent-text, #fff); }
.doc-box textarea { display: block; width: 100%; }
.doc-box .btn { margin-top: 8px; }
.codeblock { background: var(--bg-secondary); border: 1px solid var(--border); border-radius: var(--radius-sm); padding: 14px; font-family: var(--font-mono); font-size: 12px; line-height: 1.6; overflow-x: auto; white-space: pre; }

/* Save bar */
.save-bar { position: sticky; bottom: 0; left: 0; right: 0; display: flex; align-items: center; gap: 12px; justify-content: flex-end; padding: 14px 20px; background: var(--bg-card); border-top: 1px solid var(--border); box-shadow: 0 -4px 12px rgba(26,34,51,.06); z-index: 10; }
.save-msg { font-size: 12px; color: var(--success, #16a34a); }
.save-msg.err { color: var(--danger, #dc2626); }

/* Tags */
.tag-ok { background: var(--success-bg, #e9f9ef); color: var(--success, #16a34a); border: 1px solid var(--border); padding: 3px 10px; border-radius: 999px; font-size: 11px; font-weight: 600; }
.tag-warn { background: var(--warning-bg, #fef4e6); color: var(--warning, #d97706); border: 1px solid var(--border); padding: 3px 10px; border-radius: 999px; font-size: 11px; font-weight: 600; }
.tag-info { background: var(--bg-tertiary, #eef1f6); color: var(--text-secondary); border: 1px solid var(--border); padding: 3px 10px; border-radius: 999px; font-size: 11px; }

/* Utility */
.text-secondary { color: var(--text-secondary); }
.mono { font-family: var(--font-mono); font-size: 12px; }
</style>
