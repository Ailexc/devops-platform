<template>
  <div class="apply-page">
    <!-- 页面标题 -->
    <div class="page-header">
      <div class="page-header-left">
        <div class="page-header-back" @click="goBack">
          <el-icon><ArrowLeft /></el-icon>
        </div>
        <div>
          <h1>发起申请</h1>
          <p class="page-header-desc">选择要发起的流程，填写表单后提交</p>
        </div>
      </div>
    </div>

    <!-- 步骤指示器 -->
    <div class="steps-bar">
      <div class="step" :class="{ active: step >= 0, done: step > 0 }">
        <div class="step__number">
          <el-icon v-if="step > 0"><Check /></el-icon>
          <span v-else>1</span>
        </div>
        <span class="step__label">选择流程</span>
      </div>
      <div class="step__line" :class="{ active: step > 0 }"></div>
      <div class="step" :class="{ active: step >= 1, done: step > 1 }">
        <div class="step__number">
          <el-icon v-if="step > 1"><Check /></el-icon>
          <span v-else>2</span>
        </div>
        <span class="step__label">填写表单</span>
      </div>
      <div class="step__line" :class="{ active: step > 1 }"></div>
      <div class="step" :class="{ active: step >= 2, done: step > 2 }">
        <div class="step__number">
          <el-icon v-if="step > 2"><Check /></el-icon>
          <span v-else>3</span>
        </div>
        <span class="step__label">审批预览</span>
      </div>
      <div class="step__line" :class="{ active: step > 2 }"></div>
      <div class="step" :class="{ active: step >= 3 }">
        <div class="step__number">4</div>
        <span class="step__label">提单预检</span>
      </div>
    </div>

    <!-- 步骤 1：选择流程 -->
    <div v-if="step === 0" class="content-card">
      <div class="content-card-header">
        <div class="content-card-title">
          <span class="content-card-bar"></span>
          选择流程
        </div>
      </div>
      <div class="content-card-body">
        <div v-loading="loading" class="definition-grid">
          <div
            v-for="def in definitions"
            :key="def.id"
            class="definition-card"
            :class="{ selected: selectedId === def.id }"
            @click="selectDefinition(def)"
          >
            <div class="def-icon">
              <el-icon :size="28"><component :is="iconMap[def.icon] || Document" /></el-icon>
            </div>
            <div class="def-info">
              <div class="def-name">{{ def.name }}</div>
              <div class="def-desc">{{ def.description || '暂无描述' }}</div>
            </div>
            <el-tag size="small" effect="plain" class="def-tag">{{ categoryLabel(def.category) }}</el-tag>
          </div>

          <el-empty
            v-if="!loading && definitions.length === 0"
            description="暂无可发起的流程，请联系管理员配置"
          />
        </div>

        <div class="card-footer">
          <el-button type="primary" size="large" :disabled="!selectedId" @click="step = 1">
            下一步：填写表单
            <el-icon><ArrowRight /></el-icon>
          </el-button>
        </div>
      </div>
    </div>

    <!-- 步骤 2：填写表单 -->
    <div v-else-if="step === 1" class="content-card">
      <div class="content-card-header">
        <div class="content-card-title">
          <span class="content-card-bar"></span>
          填写表单
        </div>
        <div class="content-card-actions">
          <el-button text @click="step = 0">
            <el-icon><ArrowLeft /></el-icon>
            重新选择
          </el-button>
          <span class="current-def-badge">{{ currentDefinition?.name }}</span>
        </div>
      </div>
      <div class="content-card-body">
        <el-form
          ref="formRef"
          :model="form"
          :rules="rules"
          label-width="0"
          class="apply-form"
        >
          <div class="form-group">
            <label class="form-label">申请标题 <span class="required">*</span></label>
            <el-input
              v-model="form.title"
              placeholder="请输入申请标题，简要描述你的需求"
              size="large"
              maxlength="100"
              show-word-limit
            />
          </div>

          <template v-if="currentDefinition?.form_schema?.rules?.length">
            <div class="form-section">
              <div class="form-section__title">
                <span class="form-section__bar"></span>
                表单内容
              </div>
              <FormRenderer
                v-model="form.form_data"
                :rules="currentDefinition.form_schema.rules"
                :options="currentDefinition.form_schema.options || {}"
              />
            </div>
          </template>
          <el-empty
            v-else
            description="该流程未配置表单，可直接提交"
            :image-size="60"
          />

          <div class="form-actions">
            <el-button size="large" @click="step = 1">上一步</el-button>
            <el-button type="primary" size="large" :loading="previewing" @click="nextToPreview" class="submit-btn">
              <el-icon><ArrowRight /></el-icon>
              下一步：预览审批路径
            </el-button>
          </div>
        </el-form>
      </div>
    </div>

    <!-- 步骤 3：审批路径预览 -->
    <div v-else-if="step === 2" class="content-card">
      <div class="content-card-header">
        <div class="content-card-title">
          <span class="content-card-bar"></span>
          审批路径预览
        </div>
        <div class="content-card-actions">
          <el-button text @click="step = 1">
            <el-icon><ArrowLeft /></el-icon>
            上一步
          </el-button>
          <span class="current-def-badge">{{ currentDefinition?.name }}</span>
        </div>
      </div>
      <div class="content-card-body">
        <el-alert
          v-if="previewError"
          type="error"
          :title="previewError"
          show-icon
          class="preview-alert"
        />

        <div v-else-if="previewing" v-loading="true" class="preview-loading" />

        <template v-else-if="flowPath.length">
          <div class="preview-tip">
            <el-icon><InfoFilled /></el-icon>
            <span>以下为根据表单数据计算出的审批路径；点击节点查看详情，提交后将按此流程流转</span>
          </div>
          <div class="pc-split">
            <div class="pc-split-left">
              <div class="flow-preview">
                <template v-for="(node, idx) in flowPath" :key="node.key">
                  <div
                    class="preview-node"
                    :class="['preview-node--' + node.type, { clickable: true, 'is-active': previewSelKey === node.key }]"
                    @click="selectPreviewNode(node)"
                  >
                    <div class="preview-node__icon">
                      <el-icon :size="18"><component :is="nodeIcon(node.type)" /></el-icon>
                    </div>
                    <div class="preview-node__info">
                      <div class="preview-node__name">{{ node.name }}</div>
                      <div class="preview-node__meta">
                        <span class="preview-node__type">{{ node.type_label }}</span>
                        <span v-if="node.summary" class="preview-node__summary">{{ node.summary }}</span>
                      </div>
                    </div>
                  </div>
                  <div v-if="idx < flowPath.length - 1" class="preview-line"></div>
                </template>
              </div>
            </div>
            <div class="pc-split-right">
              <div v-if="previewSelNode" class="pv-detail-card">
                <div class="pv-detail-head">
                  <span class="pv-detail-name">{{ previewSelNode.name }}</span>
                  <el-tag size="small" effect="plain">{{ previewSelNode.type_label }}</el-tag>
                </div>
                <div class="pv-detail-body">
                  <template v-if="previewSelNode.type === 'approve'">
                    <div class="pv-detail-row">
                      <span class="pv-detail-label">审批方式</span>
                      <b>{{ previewSelNode.detail?.approval_type?.label || '—' }}</b>
                    </div>
                    <div class="pv-detail-row">
                      <span class="pv-detail-label">审批人</span>
                      <b>{{ previewSelNode.detail?.approvers || '—' }}</b>
                    </div>
                  </template>
                  <template v-else-if="previewSelNode.type === 'handle'">
                    <div class="pv-detail-row">
                      <span class="pv-detail-label">办理人</span>
                      <b>{{ previewSelNode.detail?.handlers || '—' }}</b>
                    </div>
                    <div class="pv-detail-row">
                      <span class="pv-detail-label">执行方式</span>
                      <b>{{ previewSelNode.detail?.mode?.label || '—' }}</b>
                    </div>
                    <div class="pv-detail-row">
                      <span class="pv-detail-label">任务编排</span>
                      <b>{{ previewSelNode.detail?.execution_mode?.label || '—' }} · {{ previewSelNode.detail?.action_count ?? 0 }} 个动作</b>
                    </div>
                    <div class="pv-detail-row">
                      <span class="pv-detail-label">任务列表</span>
                      <div class="pv-detail-actions">
                        <div v-for="a in previewSelNode.detail?.actions || []" :key="a.key" class="pv-action-tag">
                          {{ a.name }} <span class="pv-cap">{{ a.capability }}</span>
                        </div>
                      </div>
                    </div>
                  </template>
                  <template v-else-if="previewSelNode.type === 'cc'">
                    <div class="pv-detail-row">
                      <span class="pv-detail-label">抄送人</span>
                      <b>{{ previewSelNode.detail?.ccs || '—' }}</b>
                    </div>
                  </template>
                  <template v-else>
                    <div class="pv-detail-empty">
                      {{ previewSelNode.type === 'start' ? '发起节点：流程起点，记录申请人信息' : '结束节点：流程在此终止' }}
                    </div>
                  </template>
                </div>
              </div>
              <el-empty v-else description="请选择左侧节点" :image-size="50" />
            </div>
          </div>
        </template>

        <el-empty v-else description="未计算出审批路径" :image-size="60" />

        <div class="form-actions">
          <el-button size="large" @click="step = 1">上一步</el-button>
          <el-button type="primary" size="large" :loading="prechecking" @click="nextToPrecheck" class="submit-btn">
            <el-icon><ArrowRight /></el-icon>
            下一步：提单预检
          </el-button>
        </div>
      </div>
    </div>

    <!-- 步骤 4：提单预检与预演 -->
    <div v-else class="content-card">
      <div class="content-card-header">
        <div class="content-card-title">
          <span class="content-card-bar"></span>
          提单预检与预演
        </div>
        <div class="content-card-actions">
          <el-button text @click="step = 2">
            <el-icon><ArrowLeft /></el-icon>
            上一步
          </el-button>
          <span class="current-def-badge">{{ currentDefinition?.name }}</span>
        </div>
      </div>
      <div class="content-card-body">
        <el-alert v-if="precheckError" type="error" :title="precheckError" show-icon class="preview-alert" />
        <div v-else-if="prechecking" v-loading="true" class="preview-loading" />
        <template v-else-if="precheck">
          <!-- 汇总横幅 -->
          <div class="pc-banner" :class="'pc-banner--' + bannerLevel">
            <span class="pc-banner-title">{{ bannerTitle }}</span>
            <span class="pc-banner-stats">
              {{ precheck.summary.total }} 检查项 · {{ precheck.summary.passed }} 通过 ·
              {{ precheck.summary.warnings }} 警告 · {{ precheck.summary.errors }} 错误
            </span>
          </div>

          <!-- 基础校验折叠（回填表单值） -->
          <el-collapse class="pc-collapse">
            <el-collapse-item title="表单基础校验（回填你所填写的表单内容 + 校验结果 —— 配置层已约束，前端拦截 + 后端兜底）">
              <div v-for="cat in precheck.base.categories" :key="cat.name">
                <div class="pc-cat-name">{{ cat.name }}</div>
                <div v-for="c in cat.checks" :key="c.name" class="pc-base-item">
                  <span :class="c.status === 'passed' ? 'pc-ok' : 'pc-err'">{{ c.status === 'passed' ? '✓' : '✕' }}</span>
                  <span class="pc-base-name">{{ c.name }}</span>
                  <span class="pc-base-value" :class="{ 'is-empty': !c.value }">{{ c.value || '（未填写）' }}</span>
                  <span class="pc-base-msg" :class="{ 'is-err': c.status !== 'passed' }">{{ c.message }}</span>
                </div>
              </div>
            </el-collapse-item>
          </el-collapse>

          <!-- 业务规则命中 -->
          <div class="pc-section-title">业务规则预检</div>
          <div v-if="!precheck.rules.length" class="pc-empty">未配置业务规则</div>
          <div v-for="r in precheck.rules" :key="r.rule_id" class="pc-rule" :class="'pc-rule--' + (r.passed ? 'passed' : r.level)">
            <div class="pc-rule-head">
              <span class="pc-rule-id">{{ r.rule_id }}</span>
              <span class="pc-rule-name">{{ r.name }}</span>
              <el-tag size="small" :type="r.passed ? 'success' : r.level === 'error' ? 'danger' : 'warning'" effect="light">
                {{ r.passed ? '通过' : r.level === 'error' ? '拦截' : '警告' }}
              </el-tag>
            </div>
            <div v-if="!r.passed" class="pc-rule-detail">
              <!-- 判定依据：实际取值对比 -->
              <div v-if="r.detail && r.detail.conditions && r.detail.conditions.length" class="pc-rule-cond">
                <div v-for="(cd, ci) in r.detail.conditions" :key="ci" class="pc-cond-line">
                  <span class="pc-cond-src">{{ cd.source_label }}</span>
                  <b class="pc-cond-val">{{ cd.lhs_value }}</b>
                  <span class="pc-cond-op">{{ cd.op_label }}</span>
                  <template v-if="cd.ref_label">
                    <span class="pc-cond-src">{{ cd.ref_label }}</span>
                  </template>
                  <b class="pc-cond-val">{{ cd.rhs_value }}</b>
                </div>
              </div>
              <div class="pc-rule-msg">{{ r.message }}</div>
              <div class="pc-rule-sugg">建议：{{ r.suggestion }}</div>
            </div>
          </div>

          <!-- 数据来源说明 -->
          <div class="pc-source-note">
            <el-icon style="flex-shrink:0;margin-top:2px"><InfoFilled /></el-icon>
            <div class="pc-source-text">
              <b>判定依据：</b>每条规则 = 表单字段与业务上下文实时对比（见规则下方明细）。<br/>
              <b>真实环境：</b>后端在预检时调用外部系统接口（CMDB 配额 / 预算系统 / 监控 / 网络拓扑 / 历史工单）获取<b>实时数据</b>再判定。<br/>
              <b>本 Demo：</b>业务上下文为内置模拟值（ContextProvider Mock），用于演示规则能力；接入真实系统时仅替换数据源，规则无需改动。
            </div>
          </div>

          <!-- 审批路径 + 办理节点 Dry Run -->
          <div class="pc-section-title">审批路径 · 办理节点 Dry Run（点击「办理」节点查看对应任务）</div>
          <div class="pc-split">
            <div class="pc-split-left">
              <div class="flow-preview">
                <template v-for="(node, idx) in flowPath" :key="node.key">
                  <div
                    class="preview-node"
                    :class="['preview-node--' + node.type, { clickable: node.type === 'handle', 'is-active': selectedHandleKey === node.key }]"
                    @click="selectHandle(node)"
                  >
                    <div class="preview-node__icon">
                      <el-icon :size="18"><component :is="nodeIcon(node.type)" /></el-icon>
                    </div>
                    <div class="preview-node__info">
                      <div class="preview-node__name">{{ node.name }}</div>
                      <div class="preview-node__meta">
                        <span class="preview-node__type">{{ node.type_label }}</span>
                        <span v-if="node.summary" class="preview-node__summary">{{ node.summary }}</span>
                      </div>
                    </div>
                  </div>
                  <div v-if="idx < flowPath.length - 1" class="preview-line"></div>
                </template>
              </div>
            </div>
            <div class="pc-split-right">
              <div v-if="selectedDryTasks.length">
                <div v-for="(t, i) in selectedDryTasks" :key="t.key" class="pc-dry">
                  <div class="pc-dry-head">
                    <span class="pc-dry-seq">{{ i + 1 }}</span>
                    <span class="pc-dry-name">{{ t.name }}</span>
                    <el-tag size="small" effect="plain">{{ t.capability }}</el-tag>
                    <el-tag size="small" :type="t.status === 'success' ? 'success' : t.status === 'warning' ? 'warning' : 'danger'">{{ t.statusText }}</el-tag>
                  </div>
                  <div class="pc-dry-body">
                    <div class="pc-dry-col">
                      <div class="pc-dry-col-title">输入（字段绑定）</div>
                      <div v-for="(v, k) in t.input" :key="k" class="pc-dry-kv"><span>{{ k }}</span><b>{{ v ?? '—' }}</b></div>
                    </div>
                    <div class="pc-dry-col">
                      <div class="pc-dry-col-title">输出</div>
                      <div v-for="(v, k) in t.output" :key="k" class="pc-dry-kv"><span>{{ k }}</span><b>{{ v ?? '—' }}</b></div>
                    </div>
                    <div class="pc-dry-col">
                      <div class="pc-dry-col-title">执行日志</div>
                      <div v-for="(l, li) in t.logs" :key="li" class="pc-dry-log">
                        <span class="pc-dry-time">{{ l.time }}</span>
                        <span :class="'pc-dry-lvl--' + l.level">{{ l.msg }}</span>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
              <el-empty v-else description="该节点无自动化任务" :image-size="50" />
            </div>
          </div>
        </template>

        <div class="form-actions">
          <el-button size="large" @click="step = 2">上一步</el-button>
          <el-button
            type="primary" size="large" :loading="submitting" :disabled="precheckBlocked" @click="submit" class="submit-btn"
          >
            <el-icon><Promotion /></el-icon>
            {{ precheckBlocked ? '预检未通过' : '提交申请' }}
          </el-button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import {
  ArrowLeft, ArrowRight, Promotion, Document, Check, InfoFilled
} from '@element-plus/icons-vue'
import {
  getDefinitions, getDefinition, startProcess, previewPath,
  previewCheck, submitCheck
} from '@/api/modules/process'
import { loadOrgan } from '@/api/modules/organ'
import { useAuthStore } from '@/stores/auth'
import { useOrganStore } from '@/stores'
import FormRenderer from '@/components/FormRenderer/FormRenderer.vue'

const router = useRouter()
const authStore = useAuthStore()
const organStore = useOrganStore()

const step = ref(0)
const loading = ref(false)
const submitting = ref(false)
const previewing = ref(false)
const prechecking = ref(false)
const flowPath = ref([])
const previewError = ref('')
const precheck = ref(null)
const precheckError = ref('')
const selectedHandleKey = ref('')
const previewSelKey = ref('')
const definitions = ref([])
const currentDefinition = ref(null)
const selectedId = ref('')
const formRef = ref(null)

const form = reactive({
  title: '',
  form_data: {}
})

const rules = {
  title: [
    { required: true, message: '请输入申请标题', trigger: 'blur' },
    { min: 2, max: 100, message: '标题长度为 2-100 个字符', trigger: 'blur' }
  ]
}

const iconMap = {
  document: Document, edit: Document, calendar: Document,
  user: Document, folder: Document, money: Document
}

// 审批路径预览节点图标（全局注册的 Element Plus 图标名）
const nodeIconMap = {
  start: 'Promotion',
  approve: 'Checked',
  cc: 'ChatDotRound',
  handle: 'Setting',
  end: 'CircleCheckFilled'
}
const nodeIcon = (type) => nodeIconMap[type] || 'Document'

// ---- 预检结果派生 ----
const bannerLevel = computed(() => {
  const s = precheck.value?.summary
  if (!s) return 'ok'
  if (s.errors > 0 || !s.base_passed) return 'error'
  if (s.warnings > 0) return 'warning'
  return 'ok'
})
const bannerTitle = computed(() => {
  const s = precheck.value?.summary
  if (!s) return ''
  if (s.errors > 0 || !s.base_passed) return `预检未通过（${s.errors} 个业务规则错误${!s.base_passed ? '，基础校验未通过' : ''}）`
  if (s.warnings > 0) return `预检通过（有 ${s.warnings} 个警告）`
  return '预检全部通过，可放心提交'
})
const precheckBlocked = computed(() => !!precheck.value?.summary?.blocked)

// 当前选中办理节点的 Dry Run 任务
const selectedDryTasks = computed(() => {
  const dry = precheck.value?.dryrun || []
  const node = dry.find(x => x.node_key === selectedHandleKey.value)
  return node ? (node.tasks || []) : []
})

const selectHandle = (node) => {
  if (node.type === 'handle') selectedHandleKey.value = node.key
}

// ---- 审批预览（第 3 步）节点详情 ----
const previewSelNode = computed(() => flowPath.value.find(n => n.key === previewSelKey.value) || flowPath.value[0] || null)
const selectPreviewNode = (node) => {
  previewSelKey.value = node.key
}

const categoryLabel = (category) => {
  const labels = { general: '通用', hr: '人事', finance: '财务', admin: '行政', it: 'IT' }
  return labels[category] || '通用'
}

const goBack = () => {
  router.push('/')
}

const fetchDefinitions = async () => {
  loading.value = true
  try {
    const response = await getDefinitions({ status: 'published', page: 1, page_size: 100 })
    const data = response?.data ?? response
    const list = Array.isArray(data) ? data : (data?.results || [])
    definitions.value = list.filter(isAllowedDefinition)
  } catch (error) {
    console.error('获取流程列表失败:', error)
    ElMessage.error('获取流程列表失败')
  } finally {
    loading.value = false
  }
}

// 校验当前用户是否在流程的提交范围内（与后端规则一致）
const isAllowedDefinition = (def) => {
  const user = authStore.user
  if (!user) return false
  const scope = def.submit_scope
  // 不允许人员提交的流程不在申请页面展示
  if (scope === 'none') return false
  const ids = def.submit_scope_ids || []
  if (scope === 'all' || !scope) return true

  if (scope === 'specific_dept') {
    const deptIds = new Set([user.department])
    // 沿上级部门链查找：指定了上级部门时下属成员也可提交
    let parent = organStore.allDepts.find(d => d.id === user.department)?.parent
    while (parent) {
      deptIds.add(parent)
      parent = organStore.allDepts.find(d => d.id === parent)?.parent
    }
    return ids.some(id => deptIds.has(id))
  }

  if (scope === 'specific_role') {
    const roleIds = user.role_ids || []
    return ids.some(id => roleIds.includes(id))
  }
  return true
}

const selectDefinition = (def) => {
  selectedId.value = def.id
  currentDefinition.value = def
}

// 下一步：根据表单数据预计算审批路径并进入预览
const nextToPreview = async () => {
  const valid = await formRef.value.validate().catch(() => false)
  if (!valid) return
  previewing.value = true
  previewError.value = ''
  flowPath.value = []
  try {
    const resp = await previewPath(selectedId.value, { form_data: form.form_data })
    const data = resp?.data ?? resp
    flowPath.value = data?.path || []
    previewSelKey.value = flowPath.value[0]?.key || ''
    if (!flowPath.value.length) {
      previewError.value = '未计算出审批路径，请检查流程配置'
    }
    step.value = 2
  } catch (error) {
    console.error('预览审批路径失败:', error)
    previewError.value = '预览审批路径失败，请稍后重试'
  } finally {
    previewing.value = false
  }
}

// 下一步：提单预检（基础校验 + 业务规则 + 办理节点 Dry Run）
const nextToPrecheck = async () => {
  prechecking.value = true
  precheckError.value = ''
  precheck.value = null
  selectedHandleKey.value = ''
  try {
    const resp = await previewCheck(selectedId.value, { form_data: form.form_data })
    const data = resp?.data ?? resp
    precheck.value = data
    const dry = data?.dryrun || []
    const first = dry.find(x => (x.tasks || []).length)
    if (first) selectedHandleKey.value = first.node_key
    step.value = 3
  } catch (error) {
    console.error('提单预检失败:', error)
    precheckError.value = '提单预检失败，请稍后重试'
  } finally {
    prechecking.value = false
  }
}

const submit = async () => {
  if (formRef.value) {
    const valid = await formRef.value.validate().catch(() => false)
    if (!valid) return
  }

  submitting.value = true
  try {
    // 提交前权威复检（防绕过）：error 级规则命中或基础校验失败则拒绝
    const chk = await submitCheck(selectedId.value, { form_data: form.form_data })
    const chkData = chk?.data ?? chk
    if (chkData?.summary?.blocked) {
      ElMessage.warning('提单预检未通过，请根据提示修改后重试')
      return
    }

    await startProcess({
      definition_id: selectedId.value,
      title: form.title,
      form_data: form.form_data
    })
    ElMessage.success('申请提交成功')
    router.push('/my/applications')
  } catch (error) {
    console.error('提交申请失败:', error)
    if (error?.response?.data?.detail) {
      ElMessage.error(error.response.data.detail)
    } else {
      ElMessage.error('提交失败，请重试')
    }
  } finally {
    submitting.value = false
  }
}

onMounted(() => {
  fetchDefinitions()
  loadOrgan()
})
</script>

<style scoped lang="scss">
.apply-page {
  padding: 24px;
  background: var(--ticket-bg, #F7F8FA);
  min-height: 100%;
  max-width: 1000px;
  margin: 0 auto;
}

/* 页面标题 */
.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
}
.page-header-left {
  display: flex;
  align-items: center;
  gap: 12px;
}
.page-header-back {
  width: 36px; height: 36px;
  border-radius: var(--border-radius-medium, 8px);
  border: 1px solid var(--border-color, #E5E6EB);
  background: #fff;
  display: flex; align-items: center; justify-content: center;
  cursor: pointer; font-size: 16px; color: var(--text-regular, #4E5969);
  transition: all 0.2s;
  &:hover { border-color: var(--primary-color, #409EFF); color: var(--primary-color, #409EFF); }
}
.page-header h1 {
  font-size: 22px; font-weight: 700; color: var(--text-primary, #1D2129);
  margin: 0; line-height: 1.3;
}
.page-header-desc {
  font-size: 13px; color: var(--text-secondary, #86909C); margin: 2px 0 0;
}

/* 步骤条 */
.steps-bar {
  display: flex; align-items: center; justify-content: center; gap: 0;
  margin-bottom: 24px; padding: 20px 0;
  background: #fff;
  border-radius: var(--ticket-radius, 12px);
  box-shadow: var(--ticket-card-shadow, 0 1px 2px rgba(0,0,0,0.04));
  border: 1px solid var(--ticket-card-border, #E5E6EB);
}
.step {
  display: flex; align-items: center; gap: 8px;
}
.step__number {
  width: 28px; height: 28px; border-radius: 50%;
  display: flex; align-items: center; justify-content: center;
  font-size: 13px; font-weight: 600;
  background: #F2F3F5; color: var(--text-secondary, #86909C);
  transition: all 0.3s;
  &.active, .step.active & {
    background: var(--primary-color, #409EFF); color: #fff;
    box-shadow: 0 2px 8px rgba(64, 158, 255, 0.3);
  }
}
.step.active .step__number,
.step.done .step__number {
  background: var(--primary-color, #409EFF); color: #fff;
}
.step.done .step__number { background: #67C23A; }
.step__label {
  font-size: 13px; color: var(--text-secondary, #86909C); font-weight: 500;
}
.step.active .step__label { color: var(--primary-color, #409EFF); font-weight: 600; }
.step.done .step__label { color: #67C23A; }
.step__line {
  width: 60px; height: 2px; background: #F2F3F5;
  margin: 0 16px; border-radius: 1px; transition: background 0.3s;
  &.active { background: var(--primary-color, #409EFF); }
}

/* 内容卡片 */
.content-card {
  background: #fff;
  border-radius: var(--ticket-radius, 12px);
  box-shadow: var(--ticket-card-shadow, 0 1px 2px rgba(0,0,0,0.04));
  border: 1px solid var(--ticket-card-border, #E5E6EB);
  overflow: hidden;
}
.content-card-header {
  display: flex; justify-content: space-between; align-items: center;
  padding: 16px 24px; border-bottom: 1px solid #F2F3F5;
}
.content-card-title {
  display: flex; align-items: center; gap: 8px;
  font-size: 15px; font-weight: 600; color: var(--text-primary, #1D2129);
}
.content-card-bar {
  width: 3px; height: 16px; background: var(--primary-color, #409EFF); border-radius: 2px;
}
.content-card-actions {
  display: flex; align-items: center; gap: 8px;
}
.current-def-badge {
  padding: 4px 12px; border-radius: 12px; font-size: 12px; font-weight: 600;
  background: var(--primary-light, #ECF5FF); color: var(--primary-color, #409EFF);
}
.content-card-body {
  padding: 24px;
}

/* 流程选择网格 */
.definition-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 16px;
  min-height: 200px;
}
.definition-card {
  display: flex; align-items: center; gap: 14px;
  padding: 16px;
  border: 2px solid var(--border-color, #E5E6EB);
  border-radius: var(--ticket-radius, 12px);
  cursor: pointer;
  transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
  &:hover {
    border-color: var(--primary-color, #409EFF);
    box-shadow: 0 4px 12px rgba(64, 158, 255, 0.12);
    transform: translateY(-2px);
  }
  &.selected {
    border-color: var(--primary-color, #409EFF);
    background: var(--primary-light, #ECF5FF);
    box-shadow: 0 0 0 3px rgba(64, 158, 255, 0.15);
  }
}
.def-icon {
  width: 48px; height: 48px;
  border-radius: var(--ticket-radius, 12px);
  background: var(--primary-light, #ECF5FF);
  color: var(--primary-color, #409EFF);
  display: flex; align-items: center; justify-content: center; flex-shrink: 0;
}
.def-info {
  flex: 1; min-width: 0;
}
.def-name {
  font-size: 15px; font-weight: 600; color: var(--text-primary, #1D2129); margin-bottom: 4px;
}
.def-desc {
  font-size: 12px; color: var(--text-secondary, #86909C);
  overflow: hidden; text-overflow: ellipsis; white-space: nowrap;
}
.def-tag { flex-shrink: 0; }

.card-footer {
  display: flex; justify-content: flex-end;
  margin-top: 20px; padding-top: 20px; border-top: 1px solid #F2F3F5;
}

/* 表单 */
.apply-form {
  .form-group { margin-bottom: 20px; }
  .form-label {
    display: block; font-size: 14px; font-weight: 600;
    color: var(--text-primary, #1D2129); margin-bottom: 8px;
  }
  .required { color: #F53F3F; }
}
.form-section {
  margin: 24px 0;
}
.form-section__title {
  display: flex; align-items: center; gap: 8px;
  font-size: 15px; font-weight: 600; color: var(--text-primary, #1D2129);
  margin-bottom: 16px;
}
.form-section__bar {
  width: 3px; height: 16px; background: var(--primary-color, #409EFF); border-radius: 2px;
}
.form-actions {
  display: flex; justify-content: flex-end; gap: 12px;
  margin-top: 24px; padding-top: 24px; border-top: 1px solid #F2F3F5;
}
.submit-btn { min-width: 120px; }

/* 审批路径预览 */
.preview-alert {
  margin-bottom: 16px;
}
.preview-loading {
  min-height: 200px;
}
.preview-tip {
  display: flex; align-items: center; gap: 8px;
  padding: 10px 14px; margin-bottom: 20px;
  border-radius: 8px; font-size: 13px;
  background: var(--primary-light, #ECF5FF);
  color: var(--primary-color, #409EFF);
}
.flow-preview {
  display: flex; flex-direction: column; align-items: center;
  padding: 8px 0 0;
}
.preview-node {
  display: flex; align-items: center; gap: 12px;
  width: 100%; max-width: 420px;
  padding: 12px 16px;
  border: 1px solid var(--border-color, #E5E6EB);
  border-radius: 10px;
  background: #fff;
  transition: all 0.2s;
}
.preview-node__icon {
  width: 34px; height: 34px; border-radius: 50%;
  display: flex; align-items: center; justify-content: center;
  background: var(--primary-light, #ECF5FF);
  color: var(--primary-color, #409EFF);
  flex-shrink: 0;
}
.preview-node--end .preview-node__icon {
  background: #F0F9EB; color: #67C23A;
}
.preview-node--approve .preview-node__icon {
  background: #FFF7E6; color: #E6A23C;
}
.preview-node--handle .preview-node__icon {
  background: #F4F0FF; color: #722ED1;
}
.preview-node__info {
  flex: 1; min-width: 0;
}
.preview-node__name {
  font-size: 14px; font-weight: 600; color: var(--text-primary, #1D2129);
}
.preview-node__meta {
  display: flex; align-items: center; gap: 8px; margin-top: 2px;
  font-size: 12px;
}
.preview-node__type {
  padding: 1px 8px; border-radius: 10px;
  background: #F2F3F5; color: #86909C; flex-shrink: 0;
}
.preview-node__summary {
  color: #86909C; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;
}
.preview-line {
  width: 2px; height: 20px;
  background: linear-gradient(to bottom, #C9CDD4, #E5E6EB);
}

/* 办理节点可点击 */
.preview-node.clickable { cursor: pointer; }
.preview-node.clickable:hover { border-color: var(--primary-color, #409EFF); box-shadow: 0 2px 8px rgba(64, 158, 255, 0.15); }
.preview-node.is-active { border-color: var(--primary-color, #409EFF); background: var(--primary-light, #ECF5FF); }

/* 提单预检 */
.pc-banner {
  display: flex; justify-content: space-between; align-items: center; gap: 12px; flex-wrap: wrap;
  padding: 14px 18px; border-radius: 10px; margin-bottom: 16px; border: 1px solid;
}
.pc-banner--ok { border-color: #b7eb8f; background: #f0f9eb; }
.pc-banner--warning { border-color: #e6d4a8; background: #fdf6ec; }
.pc-banner--error { border-color: #f3c1c1; background: #fef0f0; }
.pc-banner-title { font-size: 15px; font-weight: 600; }
.pc-banner-stats { font-size: 12px; color: #4e5969; }
.pc-collapse { margin-bottom: 12px; }
.pc-cat-name { font-size: 12px; color: #86909c; font-weight: 600; margin: 6px 0 4px; }
.pc-base-item { font-size: 13px; color: #4e5969; padding: 2px 0; }
.pc-ok { color: #00b42a; font-weight: 700; margin-right: 4px; }
.pc-err { color: #f53f3f; font-weight: 700; margin-right: 4px; }
.pc-section-title { font-size: 15px; font-weight: 600; color: #1d2129; margin: 18px 0 10px; display: flex; align-items: center; gap: 8px; }
.pc-empty { font-size: 13px; color: #86909c; padding: 12px 0; }
.pc-rule {
  border: 1px solid #e5e6eb; border-left: 3px solid #c9cdd4; border-radius: 6px;
  padding: 10px 12px; margin-bottom: 10px; background: #fbfbfc;
}
.pc-rule--passed { border-left-color: #00b42a; }
.pc-rule--warning { border-left-color: #ff7d00; background: #fffcf7; }
.pc-rule--error { border-left-color: #f53f3f; background: #fffbfa; }
.pc-rule-head { display: flex; align-items: center; gap: 8px; flex-wrap: wrap; }
.pc-rule-id { font-family: ui-monospace, Menlo, monospace; font-size: 12px; color: #165dff; background: #e8f3ff; border-radius: 4px; padding: 1px 6px; font-weight: 600; }
.pc-rule-name { font-weight: 600; font-size: 13px; }
.pc-rule-detail { margin-top: 6px; font-size: 13px; }
.pc-rule-msg { color: #4e5969; }
.pc-rule-sugg { color: #86909c; font-size: 12px; margin-top: 2px; }

/* 审批路径 + Dry Run 左右分栏 */
.pc-split { display: flex; gap: 16px; align-items: flex-start; }
.pc-split-left { flex: 0 0 300px; min-width: 260px; }
.pc-split-right { flex: 1; min-width: 0; }
@media (max-width: 760px) { .pc-split { flex-direction: column; } .pc-split-left { flex: 1 1 auto; width: 100%; } }
.pc-dry { border: 1px solid #e5e6eb; border-radius: 8px; margin-bottom: 12px; overflow: hidden; }
.pc-dry-head { display: flex; align-items: center; gap: 8px; padding: 9px 12px; background: #f7f8fa; border-bottom: 1px solid #e5e6eb; }
.pc-dry-seq { width: 20px; height: 20px; border-radius: 50%; background: #409eff; color: #fff; font-size: 12px; display: flex; align-items: center; justify-content: center; flex-shrink: 0; }
.pc-dry-name { font-weight: 600; font-size: 13px; }
.pc-dry-body { display: flex; }
.pc-dry-col { flex: 1; padding: 9px 12px; border-right: 1px solid #e5e6eb; min-width: 0; }
.pc-dry-col:last-child { border-right: none; }
.pc-dry-col-title { font-size: 12px; color: #86909c; margin-bottom: 6px; font-weight: 600; }
.pc-dry-kv { display: flex; justify-content: space-between; gap: 8px; font-size: 12px; padding: 2px 0; }
.pc-dry-kv span { color: #4e5969; }
.pc-dry-kv b { color: #1d2129; font-weight: 500; word-break: break-all; text-align: right; }
.pc-dry-log { font-size: 12px; font-family: ui-monospace, Menlo, monospace; padding: 2px 0; }
.pc-dry-time { color: #c9cdd4; margin-right: 6px; }
.pc-dry-lvl--info { color: #4e5969; }
.pc-dry-lvl--success { color: #00b42a; }
.pc-dry-lvl--warn { color: #ff7d00; }
.pc-dry-lvl--error { color: #f53f3f; }

/* 基础校验回填 */
.pc-base-item { display: flex; align-items: baseline; gap: 6px; font-size: 13px; padding: 3px 0; }
.pc-base-name { font-weight: 600; color: #1d2129; min-width: 90px; }
.pc-base-value { color: #165dff; font-weight: 600; background: #f2f7ff; border-radius: 4px; padding: 0 6px; word-break: break-all; }
.pc-base-value.is-empty { color: #c9cdd4; background: #f7f8fa; }
.pc-base-msg { color: #86909c; margin-left: auto; text-align: right; }
.pc-base-msg.is-err { color: #f53f3f; font-weight: 600; }

/* 业务规则判定明细 */
.pc-rule-cond { margin-bottom: 6px; padding: 6px 8px; background: #f7f8fa; border-radius: 6px; }
.pc-cond-line { display: flex; align-items: center; gap: 6px; font-size: 13px; padding: 2px 0; flex-wrap: wrap; }
.pc-cond-src { color: #4e5969; }
.pc-cond-val { color: #f53f3f; font-weight: 700; background: #ffece8; border-radius: 4px; padding: 0 5px; }
.pc-cond-op { color: #86909c; }

/* 数据来源说明 */
.pc-source-note {
  display: flex; gap: 8px; padding: 10px 12px; border-radius: 8px;
  background: #f7f8fa; border: 1px dashed #c9cdd4; color: #4e5969;
  font-size: 12px; line-height: 1.7; margin-top: 4px;
}
.pc-source-note .pc-source-text { flex: 1; }
.pc-source-note b { color: #1d2129; }

/* 审批预览节点详情面板（第 3 步） */
.pv-detail-card { border: 1px solid #e5e6eb; border-radius: 10px; padding: 16px; background: #fff; min-height: 180px; }
.pv-detail-head { display: flex; align-items: center; gap: 8px; margin-bottom: 14px; }
.pv-detail-name { font-size: 15px; font-weight: 600; color: #1d2129; }
.pv-detail-body { display: flex; flex-direction: column; gap: 10px; }
.pv-detail-row { display: flex; gap: 12px; font-size: 13px; align-items: flex-start; }
.pv-detail-label { color: #86909c; width: 64px; flex-shrink: 0; padding-top: 1px; }
.pv-detail-row b { color: #1d2129; font-weight: 600; }
.pv-detail-actions { display: flex; flex-direction: column; gap: 6px; flex: 1; }
.pv-action-tag { font-size: 12px; background: #f2f3f5; border-radius: 4px; padding: 4px 8px; color: #1d2129; }
.pv-cap { color: #165dff; font-family: ui-monospace, Menlo, monospace; margin-left: 6px; }
.pv-detail-empty { color: #86909c; font-size: 13px; }

/* 响应式 */
@media (max-width: 600px) {
  .apply-page { padding: 16px; }
  .content-card-body { padding: 20px; }
  .definition-grid { grid-template-columns: 1fr; }
  .steps-bar { padding: 16px; }
  .step__line { width: 32px; margin: 0 8px; }
}
</style>
