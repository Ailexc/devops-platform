<template>
  <div class="cost-page">
    <div class="page-header fade-in">
      <div class="header-content">
        <button class="back-btn" @click="$router.back()">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M19 12H5M12 19l-7-7 7-7"></path>
          </svg>
        </button>
        <div>
          <h1 class="page-title">⚙️ 规则配置</h1>
          <p class="page-subtitle">配置优化检测规则 · 决定检测范围与检测逻辑</p>
        </div>
      </div>
    </div>

    <div class="toolbar fade-in">
      <div class="toolbar-left">
        <a-button type="primary" @click="openCreate">＋ 新建规则</a-button>
        <a-button danger @click="runAll" :loading="running">
          🚀 立即检测全部
        </a-button>
      </div>
      <div class="toolbar-hint">规则由运维团队配置，平台提供规则引擎能力</div>
    </div>

    <a-spin :spinning="loading">
      <a-empty v-if="!loading && groupKeys.length === 0" description="暂无规则，点击右上角新建" style="padding: 60px" />

      <a-collapse v-else v-model:activeKey="activeKeys" class="group-collapse fade-in">
        <a-collapse-panel v-for="cloud in groupKeys" :key="cloud">
          <template #header>
            <div class="group-header">
              <span class="cloud-pill">{{ cloudLabel(cloud) }}</span>
              <span class="group-count">{{ groupRules(cloud).length }} 条规则</span>
            </div>
          </template>
          <div v-for="rule in groupRules(cloud)" :key="rule.id" class="rule-row">
            <div class="rule-icon" :style="{ background: typeColor(rule.rule_type) + '22', color: typeColor(rule.rule_type) }">
              {{ typeIcon(rule.rule_type) }}
            </div>
            <div class="rule-info">
              <div class="rule-name">
                {{ rule.name }}
                <a-tag :color="rule.is_enabled ? 'green' : 'default'" style="margin-left: 8px">
                  {{ rule.is_enabled ? '已启用' : '已禁用' }}
                </a-tag>
              </div>
              <div class="rule-desc">{{ rule.description }}</div>
              <div class="scope-tags">
                <span v-if="rule.scope.account" class="scope-tag">🔑 {{ rule.scope.account }}</span>
                <span v-if="rule.scope.region" class="scope-tag">📍 {{ rule.scope.region }}</span>
                <span v-if="rule.scope.resource_type" class="scope-tag">📦 {{ resourceTypeLabel(rule.scope.resource_type) }}</span>
                <span v-if="!rule.scope.account && !rule.scope.region && !rule.scope.resource_type" class="scope-tag muted">全部资源</span>
              </div>
            </div>
            <div class="rule-meta">
              <a-tag :color="sevColor(rule.severity)">{{ sevLabel(rule.severity) }}优先</a-tag>
              <a-switch :checked="rule.is_enabled" size="small" @change="(v: boolean) => toggleRule(rule, v)" />
              <a-button size="small" @click="openEdit(rule)">编辑</a-button>
              <a-button size="small" danger @click="removeRule(rule)">删除</a-button>
              <a-button size="small" type="primary" ghost :loading="running" @click="runOne(rule)">单独检测</a-button>
            </div>
          </div>
        </a-collapse-panel>
      </a-collapse>
    </a-spin>

    <!-- 新建/编辑规则弹窗 -->
    <a-modal
      v-model:open="modalVisible"
      :title="editing ? '编辑规则' : '新建优化规则'"
      :confirm-loading="saving"
      width="760px"
      @ok="saveRule"
      @cancel="closeModal"
    >
      <div class="form-section">🎯 检测范围（选择要检查的资源）</div>
      <a-row :gutter="16">
        <a-col :span="12">
          <div class="form-label">云厂商</div>
          <a-select v-model:value="form.scope.cloud" allow-clear placeholder="全部云厂商">
            <a-select-option value="阿里云">阿里云</a-select-option>
            <a-select-option value="AWS">AWS</a-select-option>
            <a-select-option value="腾讯云">腾讯云</a-select-option>
          </a-select>
        </a-col>
        <a-col :span="12">
          <div class="form-label">云账号</div>
          <a-select v-model:value="form.scope.account" allow-clear placeholder="全部账号">
            <a-select-option v-for="acc in accounts" :key="acc.id" :value="acc.account_name">{{ acc.account_name }}</a-select-option>
          </a-select>
        </a-col>
      </a-row>
      <a-row :gutter="16" style="margin-top: 12px">
        <a-col :span="12">
          <div class="form-label">区域</div>
          <a-select v-model:value="form.scope.region" allow-clear placeholder="全部区域">
            <a-select-option v-for="r in REGIONS" :key="r" :value="r">{{ regionLabel(r) }}</a-select-option>
          </a-select>
        </a-col>
        <a-col :span="12">
          <div class="form-label">资源类型</div>
          <a-select v-model:value="form.scope.resource_type" allow-clear placeholder="全部资源类型" @change="onResourceTypeChange">
            <a-select-option v-for="(label, key) in RESOURCE_TYPES" :key="key" :value="key">{{ label }}</a-select-option>
          </a-select>
        </a-col>
      </a-row>

      <div class="form-section" style="margin-top: 20px">🔍 检测逻辑</div>
      <a-row :gutter="16">
        <a-col :span="12">
          <div class="form-label">规则名称</div>
          <a-input v-model:value="form.name" placeholder="如：闲置主机检测" />
        </a-col>
        <a-col :span="12">
          <div class="form-label">规则类型</div>
          <a-select v-model:value="form.rule_type" @change="onTypeChange">
            <a-select-option v-for="(label, key) in RULE_TYPES" :key="key" :value="key">{{ label }}</a-select-option>
          </a-select>
        </a-col>
      </a-row>
      <a-row :gutter="16" style="margin-top: 12px">
        <a-col :span="12">
          <div class="form-label">建议优先级</div>
          <a-select v-model:value="form.severity">
            <a-select-option value="high">高</a-select-option>
            <a-select-option value="medium">中</a-select-option>
            <a-select-option value="low">低</a-select-option>
          </a-select>
        </a-col>
        <a-col :span="12">
          <div class="form-label">规则描述</div>
          <a-input v-model:value="form.description" placeholder="简要说明规则用途" />
        </a-col>
      </a-row>

      <div class="form-section" style="margin-top: 20px">条件配置</div>
      <a-row :gutter="16">
        <a-col :span="12">
          <div class="form-label">检测条件（JSON）</div>
          <a-textarea v-model:value="form.conditionsText" :rows="5" style="font-family: monospace; font-size: 12px" />
        </a-col>
        <a-col :span="12">
          <div class="form-label">建议标题模板</div>
          <a-input v-model:value="form.title_template" placeholder="{resource_name} 建议处理" />
          <div class="form-label" style="margin-top: 12px">预估节省方式</div>
          <a-select v-model:value="form.saving_type">
            <a-select-option value="spec_ratio">按规格比例</a-select-option>
            <a-select-option value="fixed">固定金额</a-select-option>
            <a-select-option value="none">不估算</a-select-option>
          </a-select>
          <div v-if="form.saving_type === 'fixed'" style="margin-top: 8px">
            <a-input-number v-model:value="form.saving_amount" :min="0" placeholder="金额(元/月)" style="width: 100%" />
          </div>
          <div v-if="form.saving_type === 'spec_ratio'" style="margin-top: 8px">
            <a-input-number v-model:value="form.saving_percent" :min="1" :max="100" placeholder="比例(%)" style="width: 100%" />
          </div>
        </a-col>
      </a-row>
    </a-modal>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted, h } from 'vue'
import { useRouter } from 'vue-router'
import { message } from 'ant-design-vue'
import { costApi, cloudAccountApi } from '@/api'
import type { OptimizationRule } from '@/types'

const loading = ref(false)
const running = ref(false)
const modalVisible = ref(false)
const editing = ref<OptimizationRule | null>(null)
const saving = ref(false)
const cloudGroups = ref<Record<string, any[]>>({})
const activeKeys = ref<string[]>([])
const accounts = ref<{ id: number; account_name: string }[]>([])
const router = useRouter()

const RESOURCE_TYPES: Record<string, string> = {
  instance: '云主机', database: '数据库', cache: '缓存', disk: '云硬盘',
  load_balancer: '负载均衡', object_storage: '对象存储', vpc: 'VPC', subnet: '子网',
}
const RULE_TYPES: Record<string, string> = {
  idle: '闲置资源检测', downsize: '规格降配建议', unused: '未使用资源',
  budget: '预算超支告警', trend: '费用趋势异常', reserved: '付费模式优化', storage: '存储优化',
}
const TYPE_ICONS: Record<string, string> = { idle: '🔴', downsize: '🟠', unused: '🔵', budget: '🟣', trend: '🟢', reserved: '💰', storage: '🗄️' }
const TYPE_COLORS: Record<string, string> = { idle: '#EF4444', downsize: '#F97316', unused: '#3B82F6', budget: '#8B5CF6', trend: '#10B981', reserved: '#F59E0B', storage: '#0EA5E9' }
const CONDITION_TEMPLATES: Record<string, any> = {
  idle: { resource_type: 'instance', status: 'stopped', min_days: 7 },
  downsize: { resource_type: 'instance', status: 'running', metrics: { avg_cpu_7d: { lt: 5 } } },
  unused: { resource_type: 'disk', status: 'available' },
  budget: { budget_usage_percent: { gte: 80 } },
  trend: { threshold_percent: 20, direction: 'increase' },
  reserved: { billing_mode: 'pay_as_you_go' },
  storage: { min_size_gb: 100 },
}
const REGIONS = ['cn-hangzhou', 'cn-beijing', 'cn-shanghai', 'us-east-1', 'ap-southeast-1']
const REGION_LABELS: Record<string, string> = {
  'cn-hangzhou': '华东1(杭州)', 'cn-beijing': '华北2(北京)', 'cn-shanghai': '华东2(上海)',
  'us-east-1': '美东1(弗吉尼亚)', 'ap-southeast-1': '东南亚(新加坡)',
}
function regionLabel(r: string) { return REGION_LABELS[r] || r }
function resourceTypeLabel(t: string) { return RESOURCE_TYPES[t] || t }
function typeIcon(t: string) { return TYPE_ICONS[t] || '⚙️' }
function typeColor(t: string) { return TYPE_COLORS[t] || '#6B7280' }
function sevLabel(s: string) { return { high: '高', medium: '中', low: '低' }[s] || s }
function sevColor(s: string) { return { high: 'red', medium: 'orange', low: 'green' }[s] || 'default' }
function cloudLabel(c: string) { return c === '全部云' ? '🌐 全部云' : c }

const groupKeys = computed(() => Object.keys(cloudGroups.value))

function groupRules(cloud: string) {
  return cloudGroups.value[cloud] || []
}

const form = reactive({
  name: '', rule_type: 'idle', severity: 'medium', description: '',
  scope: { cloud: '', account: '', region: '', resource_type: '' },
  conditionsText: '{}', title_template: '{resource_name} 建议处理',
  saving_type: 'spec_ratio', saving_amount: 200, saving_percent: 40,
})

async function load() {
  loading.value = true
  try {
    const { data } = await costApi.ruleCloudGroups()
    cloudGroups.value = data
    activeKeys.value = Object.keys(data)
  } catch { /* 静默 */ } finally { loading.value = false }
}

function onTypeChange() {
  const tpl = CONDITION_TEMPLATES[form.rule_type] || {}
  if (form.scope.resource_type) tpl.resource_type = form.scope.resource_type
  form.conditionsText = JSON.stringify(tpl, null, 2)
}
function onResourceTypeChange() {
  try {
    const obj = JSON.parse(form.conditionsText)
    if (form.scope.resource_type) obj.resource_type = form.scope.resource_type
    else delete obj.resource_type
    form.conditionsText = JSON.stringify(obj, null, 2)
  } catch {
    if (form.scope.resource_type) form.conditionsText = JSON.stringify({ resource_type: form.scope.resource_type }, null, 2)
  }
}

function openCreate() {
  editing.value = null
  Object.assign(form, {
    name: '', rule_type: 'idle', severity: 'medium', description: '',
    scope: { cloud: '', account: '', region: '', resource_type: '' },
    conditionsText: JSON.stringify(CONDITION_TEMPLATES.idle, null, 2),
    title_template: '{resource_name} 建议处理',
    saving_type: 'spec_ratio', saving_amount: 200, saving_percent: 40,
  })
  modalVisible.value = true
}

function openEdit(rule: any) {
  editing.value = rule
  Object.assign(form, {
    name: rule.name, rule_type: rule.rule_type, severity: rule.severity, description: rule.description,
    scope: { ...rule.scope },
    conditionsText: JSON.stringify(rule.conditions || {}, null, 2),
    title_template: rule.title_template,
    saving_type: rule.saving_config?.type || 'none',
    saving_amount: rule.saving_config?.amount ?? 200,
    saving_percent: rule.saving_config?.percent ?? 40,
  })
  modalVisible.value = true
}
function closeModal() { modalVisible.value = false; editing.value = null }

function buildPayload() {
  let conditions: any = {}
  try { conditions = JSON.parse(form.conditionsText) } catch { message.error('检测条件 JSON 格式错误'); return null }
  const saving_config: any = { type: form.saving_type }
  if (form.saving_type === 'fixed') saving_config.amount = form.saving_amount
  if (form.saving_type === 'spec_ratio') saving_config.percent = form.saving_percent
  return {
    name: form.name || '未命名规则',
    rule_type: form.rule_type,
    severity: form.severity,
    description: form.description,
    scope: { ...form.scope },
    conditions,
    title_template: form.title_template,
    saving_config,
  }
}

async function saveRule() {
  const payload = buildPayload()
  if (!payload) return
  saving.value = true
  try {
    if (editing.value) await costApi.updateRule(editing.value.id, payload)
    else await costApi.createRule(payload)
    message.success(editing.value ? '规则已更新' : '规则已创建')
    closeModal()
    load()
  } catch { message.error('保存失败') } finally { saving.value = false }
}

async function removeRule(rule: any) {
  try {
    await costApi.deleteRule(rule.id)
    message.success('已删除')
    load()
  } catch { message.error('删除失败') }
}

async function toggleRule(rule: any, checked: boolean) {
  try {
    await costApi.updateRule(rule.id, { ...rule, is_enabled: checked })
    rule.is_enabled = checked
  } catch { message.error('操作失败') }
}

async function runOne(rule: any) {
  running.value = true
  try {
    const { data } = await costApi.runRule(rule.id)
    message.success(`规则「${rule.name}」检测完成，匹配 ${data.matched} 个资源`)
  } catch { message.error('执行失败') } finally { running.value = false }
}

async function runAll() {
  running.value = true
  try {
    const { data } = await costApi.runAllRules()
    message.success({
      content: h('div', { style: 'display:flex;gap:12px;align-items:center' }, [
        `全量检测完成，共匹配 ${data.report.total_matched} 个资源，生成报告 ${data.report.report_no}`,
        h('a', { style: 'color:#1677ff;font-weight:600;cursor:pointer', onClick: () => router.push('/cost/reports') }, '📄 查看报告 →'),
      ]),
      key: 'runall-done',
      duration: 8,
    })
  } catch { message.error('全量检测失败') } finally { running.value = false }
}

onMounted(async () => {
  await load()
  const { data } = await cloudAccountApi.list({ page_size: 100 })
  accounts.value = data.results
})
</script>

<style scoped>
.cost-page { max-width: 1400px; margin: 0 auto; }
.page-header { display: flex; align-items: center; margin-bottom: 24px; }
.header-content { display: flex; align-items: center; gap: 16px; }
.back-btn {
  width: 40px; height: 40px; display: flex; align-items: center; justify-content: center;
  background: white; border: 1px solid var(--cm-border-default); border-radius: var(--cm-radius-md);
  color: var(--cm-text-primary); cursor: pointer; transition: all var(--cm-transition-fast);
}
.back-btn:hover { border-color: var(--cm-border-hover); background: var(--cm-bg-tertiary); }
.back-btn svg { width: 20px; height: 20px; }
.page-title { font-size: var(--cm-text-2xl); font-weight: var(--cm-font-bold); color: var(--cm-text-primary); margin: 0; }
.page-subtitle { font-size: var(--cm-text-sm); color: var(--cm-text-secondary); margin-top: 4px; }

.toolbar { display: flex; align-items: center; justify-content: space-between; margin-bottom: 16px; }
.toolbar-left { display: flex; gap: 10px; }
.toolbar-hint { font-size: var(--cm-text-xs); color: var(--cm-text-tertiary); }

.group-collapse { background: white; border: 1px solid var(--cm-border-default); border-radius: var(--cm-radius-lg); }
:deep(.ant-collapse-header) { align-items: center; }
.group-header { display: flex; align-items: center; gap: 10px; }
.cloud-pill { padding: 2px 12px; background: var(--cm-bg-tertiary); border-radius: var(--cm-radius-full); font-size: var(--cm-text-sm); font-weight: var(--cm-font-semibold); }
.group-count { font-size: var(--cm-text-xs); color: var(--cm-text-tertiary); }

.rule-row { display: flex; align-items: center; padding: 14px 12px; border-bottom: 1px solid var(--cm-bg-tertiary); transition: background var(--cm-transition-fast); }
.rule-row:last-child { border-bottom: none; }
.rule-row:hover { background: var(--cm-bg-tertiary); }
.rule-icon { width: 36px; height: 36px; border-radius: var(--cm-radius-md); display: flex; align-items: center; justify-content: center; font-size: 16px; margin-right: 14px; flex-shrink: 0; }
.rule-info { flex: 1; min-width: 0; }
.rule-name { font-size: var(--cm-text-sm); font-weight: var(--cm-font-semibold); color: var(--cm-text-primary); }
.rule-desc { font-size: var(--cm-text-xs); color: var(--cm-text-secondary); margin-top: 2px; }
.scope-tags { display: flex; flex-wrap: wrap; gap: 6px; margin-top: 6px; }
.scope-tag { padding: 1px 8px; background: var(--cm-bg-tertiary); border-radius: var(--cm-radius-sm); font-size: 11px; color: var(--cm-text-secondary); font-family: var(--cm-font-mono); }
.scope-tag.muted { color: var(--cm-text-tertiary); }
.rule-meta { display: flex; align-items: center; gap: 8px; margin-left: 12px; flex-shrink: 0; }

.form-section { font-size: var(--cm-text-sm); font-weight: var(--cm-font-semibold); color: #7C3AED; margin-bottom: 12px; padding-bottom: 8px; border-bottom: 2px solid #EDE9FE; }
.form-label { font-size: var(--cm-text-xs); font-weight: var(--cm-font-medium); color: var(--cm-text-secondary); margin-bottom: 6px; }

.fade-in { animation: fadeIn 0.3s ease; }
@keyframes fadeIn { from { opacity: 0; transform: translateY(6px); } to { opacity: 1; transform: translateY(0); } }
</style>
