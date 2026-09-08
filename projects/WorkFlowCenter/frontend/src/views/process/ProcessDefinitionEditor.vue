<template>
  <div class="process-definition-editor">
    <!-- 步骤条 -->
    <div class="wizard-steps">
      <div
        v-for="(step, index) in steps"
        :key="step.title"
        class="wizard-step"
        :class="{
          active: currentStep === index,
          finished: currentStep > index
        }"
        @click="goToStep(index)"
      >
        <div class="step-indicator">
          <el-icon v-if="currentStep > index" class="step-check">
            <Check />
          </el-icon>
          <template v-else>{{ index + 1 }}</template>
        </div>
        <div class="step-label">
          <span class="step-title">{{ step.title }}</span>
          <span class="step-desc">{{ step.description }}</span>
        </div>
        <div v-if="index < steps.length - 1" class="step-line" />
      </div>
    </div>

    <!-- 步骤内容 -->
    <div class="wizard-content">
      <!-- 步骤 1：基本信息 -->
      <div v-show="currentStep === 0" class="step-content">
        <div class="step-header">
          <h3>基本信息</h3>
          <p>配置流程的基础信息与发起范围</p>
        </div>
        <el-form
          ref="basicFormRef"
          :model="formData"
          :rules="basicRules"
          label-width="130px"
          class="basic-form"
          :class="{ 'field-highlight': highlightedField }"
        >
          <el-collapse v-model="activeCollapse">
            <!-- 基本信息 -->
            <el-collapse-item name="basic" title="基本信息">
              <el-row :gutter="24">
                <el-col :xs="24" :md="12">
                  <el-form-item
                    label="流程名称"
                    prop="name"
                    :class="{ 'is-highlighted': highlightedField === 'name' }"
                  >
                    <el-input v-model="formData.name" placeholder="请输入流程名称，如：请假申请" />
                  </el-form-item>
                </el-col>
                <el-col :xs="24" :md="12">
                  <el-form-item
                    label="唯一标识"
                    prop="key"
                    :class="{ 'is-highlighted': highlightedField === 'key' }"
                  >
                    <el-input
                      v-model="formData.key"
                      placeholder="英文标识，如 leave_request"
                      :disabled="isEdit"
                    />
                  </el-form-item>
                </el-col>
                <el-col :xs="24" :md="12">
                  <el-form-item
                    label="流程分类"
                    prop="category"
                    :class="{ 'is-highlighted': highlightedField === 'category' }"
                  >
                    <el-select v-model="formData.category" style="width: 100%">
                      <el-option
                        v-for="c in categoryOptions"
                        :key="c.value"
                        :label="c.label"
                        :value="c.value"
                      />
                    </el-select>
                  </el-form-item>
                </el-col>
                <el-col :xs="24" :md="12">
                  <el-form-item
                    label="流程分组"
                    prop="group_id"
                    :class="{ 'is-highlighted': highlightedField === 'group_id' }"
                  >
                    <el-input
                      v-model="formData.group_id"
                      placeholder="如：人事、财务（可选）"
                    />
                  </el-form-item>
                </el-col>
                <el-col :xs="24" :md="12">
                  <el-form-item
                    label="上线状态"
                    prop="launch_status"
                    :class="{ 'is-highlighted': highlightedField === 'launch_status' }"
                  >
                    <el-select v-model="formData.launch_status" style="width: 100%">
                      <el-option label="未上线" value="offline" />
                      <el-option label="调试上线" value="debug" />
                      <el-option label="正式上线" value="production" />
                    </el-select>
                  </el-form-item>
                </el-col>
                <el-col :xs="24" :md="12">
                  <el-form-item
                    label="发起人自审"
                    :class="{ 'is-highlighted': highlightedField === 'allow_self_approve' }"
                  >
                    <div class="switch-row">
                      <el-switch v-model="formData.allow_self_approve" />
                      <span class="field-tip">允许发起人审批自己的申请</span>
                    </div>
                  </el-form-item>
                </el-col>
                <el-col :xs="24">
                  <el-form-item
                    label="流程描述"
                    prop="description"
                    :class="{ 'is-highlighted': highlightedField === 'description' }"
                  >
                    <el-input
                      v-model="formData.description"
                      type="textarea"
                      :rows="3"
                      placeholder="描述该流程的用途和适用范围"
                    />
                  </el-form-item>
                </el-col>
              </el-row>
            </el-collapse-item>

            <!-- 发起人设置 -->
            <el-collapse-item name="initiator" title="发起人设置">
              <el-row :gutter="24">
                <el-col :xs="24" :md="12">
                  <el-form-item
                    label="提交范围"
                    prop="submit_scope"
                    :class="{ 'is-highlighted': highlightedField === 'submit_scope' }"
                  >
                    <el-select v-model="formData.submit_scope" style="width: 100%">
                      <el-option label="全员可提交" value="all" />
                      <el-option label="指定部门" value="specific_dept" />
                      <el-option label="指定角色" value="specific_role" />
                      <el-option label="不允许提交（仅程序发起）" value="none" />
                    </el-select>
                  </el-form-item>
                </el-col>
                <el-col
                  v-if="formData.submit_scope === 'specific_dept' || formData.submit_scope === 'specific_role'"
                  :xs="24"
                  :md="12"
                >
                  <el-form-item
                    label="指定范围"
                    prop="submit_scope_ids"
                    :class="{ 'is-highlighted': highlightedField === 'submit_scope_ids' }"
                  >
                    <UserSelector
                      v-model="formData.submit_scope_ids"
                      :modes="formData.submit_scope === 'specific_dept' ? ['dept'] : ['role']"
                      :placeholder="formData.submit_scope === 'specific_dept' ? '选择可提交的部门' : '选择可提交的角色'"
                    />
                  </el-form-item>
                </el-col>
                <el-col :xs="24" :md="12">
                  <el-form-item
                    label="流程管理员"
                    prop="admin_ids"
                    :class="{ 'is-highlighted': highlightedField === 'admin_ids' }"
                  >
                    <UserSelector
                      v-model="formData.admin_ids"
                      :modes="['user']"
                      placeholder="选择流程管理员（可多人）"
                    />
                  </el-form-item>
                </el-col>
              </el-row>
            </el-collapse-item>

            <!-- 程序发起 -->
            <el-collapse-item name="program" title="程序发起">
              <el-row :gutter="24">
                <el-col :xs="24" :md="12">
                  <el-form-item
                    label="允许程序发起"
                    :class="{ 'is-highlighted': highlightedField === 'allow_program_initiate' }"
                  >
                    <div class="switch-row">
                      <el-switch v-model="formData.allow_program_initiate" />
                      <span class="field-tip">开启后，绑定的程序可通过接口代提单</span>
                    </div>
                  </el-form-item>
                </el-col>
                <el-col v-if="formData.allow_program_initiate" :xs="24" :md="12">
                  <el-form-item
                    label="发起程序"
                    prop="initiator_app_ids"
                    :class="{ 'is-highlighted': highlightedField === 'initiator_app_ids' }"
                  >
                    <el-select
                      v-model="formData.initiator_app_ids"
                      multiple
                      filterable
                      style="width: 100%"
                      placeholder="选择可发起该流程的程序（可多选）"
                    >
                      <el-option
                        v-for="app in initiatorApps"
                        :key="app.id"
                        :label="app.name"
                        :value="app.id"
                        :disabled="!app.is_active"
                      >
                        <span>{{ app.name }}</span>
                        <span class="app-code">{{ app.code }}</span>
                      </el-option>
                    </el-select>
                    <div class="field-tip-row">
                      <span class="field-tip">程序发起时需携带程序凭证，并指定提单人</span>
                      <el-link
                        type="primary"
                        :underline="false"
                        @click="router.push('/admin/initiator-apps')"
                      >
                        管理程序
                      </el-link>
                    </div>
                  </el-form-item>
                </el-col>
              </el-row>
            </el-collapse-item>

          </el-collapse>
        </el-form>
      </div>

      <!-- 步骤 2：表单设计 -->
      <div v-show="currentStep === 1" class="step-content">
        <div class="step-header">
          <h3>表单设计</h3>
          <p>设计发起人填写的内容表单，支持拖拽组件与 AI 快速生成</p>
        </div>
        <FormBuilder v-model="formData.form_schema" />
      </div>

      <!-- 步骤 3：流程建模 -->
      <div v-show="currentStep === 2" class="step-content step-content--full">
        <div class="step-header step-header--flow">
          <h3>流程建模</h3>
          <p>绘制审批流程，配置审批人 / 抄送人 / 办理人 / 条件分支</p>
        </div>
        <ProcessFlowDesigner
          v-model="formData.definition_json"
          :form-schema="formData.form_schema"
        />
      </div>

      <!-- 步骤 4：业务规则 -->
      <div v-show="currentStep === 3" class="step-content">
        <div class="step-header">
          <h3>业务规则（提单预检）</h3>
          <p>配置提单预检规则：配额 / 容量 / 网络 / 预算 / 规格建议，表单化配置，无需手写表达式</p>
        </div>
        <RulePanel
          :rules="formData.rules_json"
          :sources="ruleMeta"
          @update:rules="formData.rules_json = $event"
        />
      </div>

      <!-- 步骤 5：检查 -->
      <div v-show="currentStep === 4" class="step-content">
        <div class="step-header">
          <h3>流程检查</h3>
          <p>发布前自检流程配置（含业务规则）；检查通过后保存草稿，再到「流程配置」列表页发布流程</p>
        </div>
        <FlowCheckPanel
          v-model="checkResult"
          :loading="checking"
          @fix="handleFix"
        />
      </div>
    </div>

    <!-- 底部操作栏 -->
    <div class="wizard-footer">
      <div class="footer-left">
        <el-button v-if="currentStep > 0" @click="prevStep">
          <el-icon><ArrowLeft /></el-icon>
          上一步
        </el-button>
      </div>
      <div class="footer-right">
        <el-button @click="discardEdit">
          放弃编辑
        </el-button>
        <el-button :loading="saving" @click="saveDraft">
          保存草稿
        </el-button>
        <el-button
          v-if="currentStep < 4"
          type="primary"
          @click="nextStep"
        >
          下一步
          <el-icon><ArrowRight /></el-icon>
        </el-button>
        <span v-else class="publish-hint">
          检查通过后，请保存草稿并到「流程配置」列表页发布流程
        </span>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  ArrowLeft, ArrowRight, Check
} from '@element-plus/icons-vue'
import {
  getDefinition, createDefinition, updateDefinition,
  validateDefinition, getRuleMeta
} from '@/api/modules/process'
import { getInitiatorApps } from '@/api/modules/initiator-apps'
import useFlowStore from '@/stores/flow'
import FormBuilder from '@/components/FormBuilder/FormBuilder.vue'
import ProcessFlowDesigner from '@/components/FlowDesigner/ProcessFlowDesigner.vue'
import FlowCheckPanel from '@/components/flow/FlowCheckPanel.vue'
import RulePanel from '@/components/flow/RulePanel.vue'
import UserSelector from '@/components/common/UserSelector.vue'

const router = useRouter()
const route = useRoute()
const flowStore = useFlowStore()

const isEdit = computed(() => !!route.params.id)
const currentStep = ref(0)
const saving = ref(false)
const checking = ref(false)
const checkResult = ref(null)
const basicFormRef = ref(null)
const activeCollapse = ref(['basic', 'initiator', 'program'])
const highlightedField = ref('')
const initiatorApps = ref([])
const ruleMeta = ref({ form: [], context: [] })

const steps = [
  { title: '基本信息', description: '流程基础配置' },
  { title: '表单设计', description: '发起表单内容' },
  { title: '流程建模', description: '审批流程绘制' },
  { title: '业务规则', description: '提单预检规则' },
  { title: '检查', description: '发布前检查' }
]

const categoryOptions = [
  { value: 'general', label: '通用' },
  { value: 'hr', label: '人事' },
  { value: 'finance', label: '财务' },
  { value: 'admin', label: '行政' },
  { value: 'it', label: 'IT' }
]

const formData = reactive({
  name: '',
  key: '',
  description: '',
  category: 'general',
  submit_scope: 'all',
  submit_scope_ids: [],
  admin_ids: [],
  group_id: '',
  allow_program_initiate: false,
  initiator_app_ids: [],
  launch_status: 'offline',
  allow_self_approve: true,
  form_schema: {
    rules: [],
    options: {}
  },
  definition_json: {
    nodeConfig: null,
    flowWidgets: [],
    workFlowDef: {},
    flowPermission: {}
  },
  rules_json: [],
  status: 'draft'
})

const basicRules = {
  name: [
    { required: true, message: '请输入流程名称', trigger: 'blur' }
  ],
  key: [
    { required: true, message: '请输入唯一标识', trigger: 'blur' },
    { pattern: /^[a-zA-Z][a-zA-Z0-9_]*$/, message: '标识只能包含字母、数字和下划线', trigger: 'blur' }
  ],
  category: [
    { required: true, message: '请选择流程分类', trigger: 'change' }
  ]
}

// 获取详情
const fetchDetail = async () => {
  if (!route.params.id) return
  try {
    const response = await getDefinition(route.params.id)
    const data = response?.data ?? response
    Object.assign(formData, {
      name: data.name || '',
      key: data.key || '',
      description: data.description || '',
      category: data.category || 'general',
      submit_scope: data.submit_scope || 'all',
      submit_scope_ids: data.submit_scope_ids || [],
      admin_ids: data.admin_ids || [],
      group_id: data.group_id || '',
      allow_program_initiate: !!data.allow_program_initiate,
      initiator_app_ids: data.initiator_app_ids || [],
      launch_status: data.launch_status || 'offline',
      allow_self_approve: data.allow_self_approve ?? true,
      form_schema: data.form_schema || { rules: [], options: {} },
      definition_json: data.definition_json || { nodeConfig: null, flowWidgets: [], workFlowDef: {}, flowPermission: {} },
      rules_json: data.rules_json || [],
      status: data.status
    })
  } catch (error) {
    console.error('获取详情失败:', error)
    ElMessage.error('获取流程详情失败')
  }
}

// 步骤导航
const goToStep = (index) => {
  if (index < currentStep.value) {
    currentStep.value = index
    highlightedField.value = ''
  }
}

const prevStep = () => {
  if (currentStep.value > 0) {
    currentStep.value--
    highlightedField.value = ''
  }
}

const nextStep = async () => {
  if (currentStep.value === 0) {
    const valid = await basicFormRef.value.validate().catch(() => false)
    if (!valid) return
  }
  currentStep.value++
  highlightedField.value = ''
  if (currentStep.value === 4) {
    runCheck()
  }
  if (currentStep.value === 3) {
    loadRuleMeta()
  }
}

// 流程检查
const runCheck = async () => {
  checking.value = true
  checkResult.value = null
  try {
    const payload = {
      name: formData.name,
      key: formData.key,
      submit_scope: formData.submit_scope,
      submit_scope_ids: formData.submit_scope_ids,
      admin_ids: formData.admin_ids,
      allow_program_initiate: formData.allow_program_initiate,
      initiator_app_ids: formData.initiator_app_ids,
      launch_status: formData.launch_status,
      allow_self_approve: formData.allow_self_approve,
      definition_json: formData.definition_json,
      form_schema: formData.form_schema,
      rules_json: formData.rules_json
    }
    const response = await validateDefinition(payload)
    checkResult.value = response.data ?? response
  } catch (error) {
    console.error('流程检查失败:', error)
    ElMessage.error('流程检查失败，请稍后重试')
  } finally {
    checking.value = false
  }
}

// 跳转修复
const handleFix = (fixAction) => {
  if (!fixAction || fixAction.type !== 'jump') return
  const stepMap = {
    step_0: 0,
    step_1: 1,
    step_2: 2
  }
  const target = stepMap[fixAction.target]
  if (target === undefined) return

  currentStep.value = target
  highlightedField.value = fixAction.field || ''

  if (target === 0 && fixAction.field) {
    const collapseMap = {
      name: 'basic', key: 'basic', category: 'basic',
      group_id: 'basic', description: 'basic',
      launch_status: 'basic', allow_self_approve: 'basic',
      allow_program_initiate: 'program', initiator_app_ids: 'program',
      submit_scope: 'initiator', submit_scope_ids: 'initiator', admin_ids: 'initiator'
    }
    const collapseName = collapseMap[fixAction.field]
    if (collapseName && !activeCollapse.value.includes(collapseName)) {
      activeCollapse.value.push(collapseName)
    }
    // 高亮闪烁后清除
    setTimeout(() => {
      highlightedField.value = ''
    }, 2600)
  }
}

// 保存
const buildPayload = () => {
  // 从 flowStore 获取最新的流程定义（用户可能在设计器中修改了但没点"保存流程配置"）
  const latestFlowDef = flowStore.flowDefinition || {}
  const definitionJson = {
    nodeConfig: latestFlowDef.nodeConfig || formData.definition_json.nodeConfig,
    flowWidgets: latestFlowDef.flowWidgets || formData.definition_json.flowWidgets,
    workFlowDef: latestFlowDef.workFlowDef || formData.definition_json.workFlowDef,
    flowPermission: latestFlowDef.flowPermission || formData.definition_json.flowPermission,
  }
  return {
    name: formData.name,
    key: formData.key,
    description: formData.description,
    category: formData.category,
    submit_scope: formData.submit_scope,
    submit_scope_ids: formData.submit_scope_ids,
    admin_ids: formData.admin_ids,
    group_id: formData.group_id,
    allow_program_initiate: formData.allow_program_initiate,
    initiator_app_ids: formData.initiator_app_ids,
    launch_status: formData.launch_status,
    allow_self_approve: formData.allow_self_approve,
    form_schema: formData.form_schema,
    definition_json: definitionJson,
    rules_json: formData.rules_json
  }
}

const save = async (silent = false) => {
  saving.value = true
  try {
    let savedId = route.params.id
    if (isEdit.value) {
      await updateDefinition(savedId, buildPayload())
      if (!silent) ElMessage.success('草稿已保存')
    } else {
      const response = await createDefinition(buildPayload())
      const data = response?.data ?? response
      savedId = data.id
      if (!silent) ElMessage.success('草稿已保存')
      router.replace(`/process-definitions/${savedId}`)
    }
    return { success: true, id: savedId }
  } catch (error) {
    console.error('保存失败:', error)
    if (!silent) ElMessage.error('保存失败')
    return { success: false, id: null }
  } finally {
    saving.value = false
  }
}

const saveDraft = async () => {
  const result = await save(false)
  // 保存草稿后自动返回列表页，由列表页统一发起发布
  if (result.success) {
    router.push('/process-definitions')
  }
}

// 放弃编辑：确认后返回列表页，不保存
const discardEdit = async () => {
  try {
    await ElMessageBox.confirm(
      '确定放弃编辑吗？未保存的修改将不会保留。',
      '放弃编辑',
      {
        confirmButtonText: '确定放弃',
        cancelButtonText: '继续编辑',
        type: 'warning'
      }
    )
    router.push('/process-definitions')
  } catch (error) {
    // 用户取消，留在编辑页
  }
}

const loadInitiatorApps = async () => {
  try {
    const response = await getInitiatorApps({ page: 1, page_size: 100 })
    const data = response?.data ?? response
    initiatorApps.value = Array.isArray(data) ? data : (data?.results || [])
  } catch (error) {
    console.error('获取发起程序列表失败:', error)
  }
}

const loadRuleMeta = async () => {
  if (!route.params.id) return
  try {
    const response = await getRuleMeta(route.params.id)
    ruleMeta.value = response?.data ?? response
  } catch (error) {
    console.error('获取规则数据源失败:', error)
  }
}

onMounted(() => {
  fetchDetail()
  loadInitiatorApps()
  loadRuleMeta()
})
</script>

<style scoped lang="scss">
.process-definition-editor {
  display: flex;
  flex-direction: column;
  min-height: calc(100vh - 60px);
  max-width: 1440px;
  margin: 0 auto;
  padding: 0 24px;
}

/* ==================== 步骤条 ==================== */
.wizard-steps {
  display: flex;
  align-items: stretch;
  background: #fff;
  border: 1px solid #e4e7ed;
  border-radius: 12px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.04);
  padding: 20px 12px 16px;
  margin: 20px 0 16px;
}

.wizard-step {
  position: relative;
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 6px;
  cursor: pointer;
  padding: 0 4px;
  text-align: center;
  user-select: none;
  transition: transform 0.2s ease;

  &:hover .step-indicator {
    box-shadow: 0 0 0 4px rgba(64, 158, 255, 0.08);
  }

  .step-indicator {
    position: relative;
    z-index: 1;
    width: 36px;
    height: 36px;
    border-radius: 50%;
    background: #fff;
    border: 2px solid #dcdfe6;
    color: #909399;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 15px;
    font-weight: 600;
    flex-shrink: 0;
    transition: all 0.3s;
  }

  .step-check {
    font-size: 18px;
  }

  .step-label {
    .step-title {
      display: block;
      font-size: 14px;
      font-weight: 500;
      color: #606266;
      transition: color 0.3s;
      white-space: nowrap;
    }

    .step-desc {
      display: block;
      font-size: 12px;
      color: #a8abb2;
      margin-top: 2px;
      white-space: nowrap;
    }
  }

  /* 连接线：从本步指示器中心连到下一步指示器中心（等宽均分） */
  .step-line {
    position: absolute;
    top: 18px; /* 指示器中心 */
    left: 50%;
    right: -50%;
    height: 2px;
    background: #e4e7ed;
    z-index: 0;
    transition: background 0.3s;
  }

  &.finished {
    .step-indicator {
      background: #409eff;
      border-color: #409eff;
      color: #fff;
    }

    .step-title {
      color: #409eff;
      font-weight: 600;
    }

    .step-line {
      background: #409eff;
    }
  }

  &.active {
    .step-indicator {
      border-color: #409eff;
      color: #409eff;
      background: #ecf5ff;
      box-shadow: 0 0 0 4px rgba(64, 158, 255, 0.12);
    }

    .step-title {
      color: #303133;
      font-weight: 600;
    }

    .step-desc {
      color: #409eff;
    }
  }
}

/* ==================== 内容区 ==================== */
.wizard-content {
  flex: 1;
  background: #fff;
  border-radius: 12px;
  border: 1px solid #ebeef5;
  padding: 24px 32px;
  min-height: 520px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.04);
}

.step-content {
  &--full {
    padding: 0 0 16px;
  }
}

.step-header {
  margin-bottom: 20px;

  h3 {
    margin: 0 0 4px;
    font-size: 18px;
    color: #303133;
    font-weight: 600;
  }

  p {
    margin: 0;
    font-size: 13px;
    color: #909399;
  }
}

/* 字段高亮（检查跳转） */
.field-highlight :deep(.el-form-item) {
  &.is-highlighted {
    animation: field-flash 1.2s ease 2;
    border-radius: 6px;
  }
}

@keyframes field-flash {
  0%, 100% {
    box-shadow: none;
    background: transparent;
  }
  50% {
    box-shadow: 0 0 0 3px rgba(64, 158, 255, 0.35);
    background: #ecf5ff;
  }
}

.field-tip {
  margin-left: 8px;
  font-size: 12px;
  color: #909399;
}

.switch-row {
  display: flex;
  align-items: center;
  min-height: 32px;
}

.field-tip-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  margin-top: 4px;

  .field-tip {
    margin-left: 0;
  }
}

.app-code {
  float: right;
  margin-left: 12px;
  font-size: 12px;
  color: #909399;
}

/* ==================== 底部操作栏 ==================== */
.wizard-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 0 24px;
  gap: 16px;

  .footer-left,
  .footer-right {
    display: flex;
    align-items: center;
    gap: 12px;
  }

  .publish-hint {
    font-size: 12px;
    color: #909399;
    background: #f4f4f5;
    border: 1px solid #ebeef5;
    border-radius: 6px;
    padding: 6px 12px;
    line-height: 1.5;
  }
}

/* ==================== 响应式 ==================== */
@media (max-width: 768px) {
  .wizard-steps {
    flex-direction: column;
    gap: 8px;
  }

  .wizard-step {
    width: 100%;
    flex: 0 0 auto;
    flex-direction: row;
    justify-content: flex-start;
    text-align: left;

    .step-line {
      display: none;
    }
  }

  .wizard-content {
    padding: 16px;
  }

  .wizard-footer {
    flex-direction: column;

    .footer-left,
    .footer-right {
      width: 100%;
      justify-content: center;
    }
  }
}
</style>
