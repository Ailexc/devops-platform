<template>
  <div class="beeflow-designer">
    <div class="beeflow-designer__toolbar">
      <div class="toolbar-info">
        <span class="toolbar-title">流程设计</span>
        <span class="toolbar-tip">点击「+」添加节点，点击节点卡片配置审批人 / 抄送人 / 办理人 / 条件分支</span>
      </div>
      <div class="toolbar-actions">
        <!-- AI 助手按钮 -->
        <el-button size="small" type="primary" plain class="ai-entry" @click="openAiPanel">
          <el-icon><MagicStick /></el-icon>
          AI 智能助理
        </el-button>
        
        <el-divider direction="vertical" />
        
        <!-- 导入导出 -->
        <el-button size="small" @click="exportJson">
          <el-icon><Download /></el-icon>
          导出 JSON
        </el-button>
        <el-button size="small" @click="importJson">
          <el-icon><Upload /></el-icon>
          导入 JSON
        </el-button>
        
        <div class="zoom-controls">
          <el-button size="small" circle :disabled="flowStore.zoomScale <= 50" @click="flowStore.zoomOut()">
            <el-icon><ZoomOut /></el-icon>
          </el-button>
          <span class="zoom-value">{{ flowStore.zoomScale }}%</span>
          <el-button size="small" circle :disabled="flowStore.zoomScale >= 200" @click="flowStore.zoomIn()">
            <el-icon><ZoomIn /></el-icon>
          </el-button>
        </div>
        <el-button size="small" @click="resetFlow">
          <el-icon><RefreshLeft /></el-icon>
          重置
        </el-button>
        <el-button size="small" type="primary" @click="saveFlow">
          <el-icon><Check /></el-icon>
          保存流程配置
        </el-button>
      </div>
    </div>

    <div class="beeflow-designer__canvas">
      <Flow v-if="ready" :key="designerKey" />
    </div>

    <!-- AI 助手抽屉 -->
    <el-drawer
      v-model="aiVisible"
      title="AI 智能助理（流程设计）"
      size="520px"
      append-to-body
      destroy-on-close
    >
      <FlowAiPromptPanel
        :current-definition="buildPayload()"
        :form-schema="formSchema"
        @apply="applyAiFlow"
      />
    </el-drawer>
  </div>
</template>

<script setup>
import { computed, nextTick, onMounted, reactive, ref, watch } from 'vue'
import { 
  Check, Download, Upload, RefreshLeft, ZoomIn, ZoomOut, MagicStick 
} from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import Flow from '@/components/flow/index.vue'
import { NODE } from '@/components/flow/common/FlowConstant'
import { useFlowStore, useOrganStore } from '@/stores'
import { loadOrgan } from '@/api/modules/organ'
import { formCreateToFlowWidgets } from '@/components/SchemaConverter/formCreateToFlowWidgets'
import FlowAiPromptPanel from '@/components/flow/FlowAiPromptPanel.vue'

const props = defineProps({
  modelValue: {
    type: Object,
    default: () => null,
  },
  formSchema: {
    type: Object,
    default: () => ({ rules: [], options: {} }),
  },
})

const emit = defineEmits(['update:modelValue'])

const flowStore = useFlowStore()
useOrganStore()

const ready = ref(false)
const designerKey = ref(0)
const aiVisible = ref(false)

const clone = (obj) => (obj == null ? obj : JSON.parse(JSON.stringify(obj)))

function createDefaultDefinition() {
  return {
    nodeConfig: {
      key: 'start',
      name: '发起人',
      type: NODE.START,
      childNode: null,
    },
    flowWidgets: formCreateToFlowWidgets(props.formSchema?.rules || []),
    workFlowDef: {
      id: 'wf_' + Date.now().toString(),
      icon: 'approval',
      name: '未命名流程',
      groupId: '',
      cancelable: 1,
      flowAdminIds: [],
    },
    flowPermission: {
      type: 0, // 0 全员可提交
      flowInitiators: [],
    },
  }
}

function initDefinition() {
  const incoming = props.modelValue
  const base = createDefaultDefinition()
  if (incoming?.nodeConfig) {
    base.nodeConfig = clone(incoming.nodeConfig)
    base.workFlowDef = { ...base.workFlowDef, ...clone(incoming.workFlowDef || {}) }
    base.flowPermission = clone(incoming.flowPermission || base.flowPermission)
  }
  // flowWidgets 始终以当前表单 schema 为准
  base.flowWidgets = formCreateToFlowWidgets(props.formSchema?.rules || [])
  flowStore.setFlowDef(base)
}

initDefinition()

onMounted(() => {
  ready.value = true
  loadOrgan()
})

// 表单变更时，同步 flowWidgets（条件分支 / 表单权限实时可用）
watch(
  () => props.formSchema?.rules,
  (rules) => {
    if (!flowStore.flowDefinition) return
    flowStore.flowDefinition.flowWidgets = formCreateToFlowWidgets(rules || [])
  },
  { deep: true }
)

// 外部（如详情回显）更新 flow JSON 时重新装载设计器
watch(
  () => props.modelValue,
  (val) => {
    if (!val || !val.nodeConfig) return
    initDefinition()
    designerKey.value += 1
  },
  { deep: false }
)

function buildPayload() {
  const def = flowStore.flowDefinition || {}
  return {
    nodeConfig: clone(def.nodeConfig),
    flowWidgets: formCreateToFlowWidgets(props.formSchema?.rules || []),
    workFlowDef: clone(def.workFlowDef),
    flowPermission: clone(def.flowPermission),
  }
}

function saveFlow() {
  const payload = buildPayload()
  emit('update:modelValue', payload)
  ElMessage.success('流程配置已保存，请点击页面右上角「保存」落库')
}

function exportJson() {
  const payload = buildPayload()
  const blob = new Blob([JSON.stringify(payload, null, 2)], { type: 'application/json' })
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = `${payload.workFlowDef?.name || 'flow'}.json`
  link.click()
  URL.revokeObjectURL(url)
}

// 导入 JSON - 支持文件选择和粘贴
function importJson() {
  ElMessageBox.confirm(
    '请选择导入方式',
    '导入流程配置',
    {
      confirmButtonText: '选择文件',
      cancelButtonText: '粘贴 JSON',
      distinguishCancelAndClose: true,
      type: 'info',
    }
  )
    .then(() => {
      // 文件选择方式
      const input = document.createElement('input')
      input.type = 'file'
      input.accept = '.json'
      input.onchange = async (e) => {
        const file = e.target.files[0]
        if (!file) return
        try {
          const text = await file.text()
          const data = JSON.parse(text)
          applyImportedJson(data)
        } catch (err) {
          ElMessage.error('JSON 解析失败: ' + err.message)
        }
      }
      input.click()
    })
    .catch((action) => {
      if (action === 'cancel') {
        // 粘贴方式
        ElMessageBox.prompt('请粘贴流程配置 JSON', '导入流程', {
          confirmButtonText: '导入',
          cancelButtonText: '取消',
          inputType: 'textarea',
          inputPlaceholder: '粘贴 JSON...',
          inputValidator: (val) => {
            if (!val?.trim()) return '请输入 JSON 内容'
            try {
              const data = JSON.parse(val)
              if (!data.nodeConfig) return 'JSON 缺少 nodeConfig 字段'
              return true
            } catch {
              return 'JSON 格式错误'
            }
          },
        })
          .then(({ value }) => {
            try {
              const data = JSON.parse(value)
              applyImportedJson(data)
            } catch (err) {
              ElMessage.error('JSON 解析失败: ' + err.message)
            }
          })
          .catch(() => {})
      }
    })
}

function applyImportedJson(data) {
  // 校验必要字段
  if (!data.nodeConfig) {
    ElMessage.error('JSON 缺少 nodeConfig 字段')
    return
  }

  ElMessageBox.confirm(
    `确定要导入流程配置吗？\n\n流程名称: ${data.workFlowDef?.name || '未命名'}\n节点数量: ${countNodes(data.nodeConfig)}`,
    '确认导入',
    {
      confirmButtonText: '确定导入',
      cancelButtonText: '取消',
      type: 'warning',
    }
  )
    .then(() => {
      // 应用导入的数据
      const payload = {
        nodeConfig: clone(data.nodeConfig),
        flowWidgets: data.flowWidgets || formCreateToFlowWidgets(props.formSchema?.rules || []),
        workFlowDef: {
          id: 'wf_' + Date.now().toString(), // 生成新 ID 避免冲突
          icon: 'approval',
          name: data.workFlowDef?.name || '导入的流程',
          groupId: '',
          cancelable: 1,
          flowAdminIds: [],
          ...(data.workFlowDef || {}),
        },
        flowPermission: data.flowPermission || { type: 0, flowInitiators: [] },
      }
      
      emit('update:modelValue', payload)
      // 重新装载设计器
      designerKey.value += 1
      ElMessage.success('流程配置导入成功')
    })
    .catch(() => {})
}

function countNodes(nodeConfig) {
  if (!nodeConfig) return 0
  let count = 1
  if (nodeConfig.childNode) count += countNodes(nodeConfig.childNode)
  if (nodeConfig.conditionNodes) {
    nodeConfig.conditionNodes.forEach((n) => {
      count += countNodes(n)
    })
  }
  return count
}

function resetFlow() {
  ElMessageBox.confirm('确定要清空当前流程，重新开始设计吗？', '重置流程', {
    confirmButtonText: '确定',
    cancelButtonText: '取消',
    type: 'warning',
  })
    .then(() => {
      initDefinition()
      designerKey.value += 1
      ElMessage.success('已重置')
    })
    .catch(() => {})
}

// ================= AI 助手 =================
const openAiPanel = () => {
  aiVisible.value = true
}

// 节点类型映射（字符串 -> 数字）
const NODE_TYPE_MAP = {
  'START': 0,
  'start': 0,
  'APPROVAL': 1,
  'approval': 1,
  'APPROVE': 1,
  'approve': 1,
  'CC': 2,
  'cc': 2,
  'COPY': 2,
  'copy': 2,
  'CONDITION': 3,
  'condition': 3,
  'ACTION': 5,
  'action': 5,
  'TRANSACT': 5,
  'transact': 5,
  'END': 9,
  'end': 9,
}

// 审批人类型映射
const ASSIGNEE_TYPE_MAP = {
  'SELF': 0,
  'self': 0,
  'SUPERIOR': 1,
  'superior': 1,
  'DEPT_LEADER': 2,
  'dept_leader': 2,
  'DEPARTMENT_LEADER': 2,
  'department_leader': 2,
  'ROLE': 3,
  'role': 3,
  'ASSIGNEE': 4,
  'assignee': 4,
  'USER': 4,
  'user': 4,
}

// 递归转换节点类型
const convertNodeTypes = (node) => {
  if (!node || typeof node !== 'object') return node
  
  // 转换 type
  if (typeof node.type === 'string') {
    node.type = NODE_TYPE_MAP[node.type] ?? node.type
  }
  
  // 关键修复：如果有 conditionNodes 数组，说明这是网关节点，type 应该是 4 (EXCLUSIVE_GATEWANY)
  if (node.conditionNodes && Array.isArray(node.conditionNodes) && node.conditionNodes.length > 0) {
    node.type = 4  // EXCLUSIVE_GATEWANY
  }
  
  // 转换 assigneeType
  if (typeof node.assigneeType === 'string') {
    node.assigneeType = ASSIGNEE_TYPE_MAP[node.assigneeType] ?? node.assigneeType
  }
  
  // 处理审批人/抄送人/办理人节点
  if ([1, 2, 5].includes(node.type)) {
    // 如果没有 assignees 数组，从 assigneeType 和 assigneeIds 创建
    if (!node.assignees && node.assigneeType !== undefined) {
      const assigneeTypeMap = {
        0: 0,  // SELF -> 发起人本人
        1: 1,  // SUPERIOR -> 上级
        2: 2,  // DEPT_LEADER -> 部门负责人
        3: 3,  // ROLE -> 角色
        4: 4,  // ASSIGNEE/USER -> 指定成员
      }
      
      node.assignees = [{
        assigneeType: assigneeTypeMap[node.assigneeType] ?? 4,
        layerType: 0,
        layer: 0,
        roles: node.assigneeType === 3 ? (node.assigneeIds || []) : [],
        assignees: node.assigneeType === 4 ? (node.assigneeIds || []) : [],
      }]
    }
    
    // 确保 assignees 是数组
    if (!node.assignees) {
      node.assignees = []
    }
  }
  
  // 处理抄送人节点的 ccs 数组
  if (node.type === 2) {
    if (!node.ccs) {
      node.ccs = node.assignees || []
    }
  }
  
  // 处理办理人节点的 transactors 数组
  if (node.type === 5) {
    if (!node.transactors) {
      node.transactors = node.assignees || []
    }
  }

  // 处理条件分支节点（type: 3）
  if (node.type === 3 && node.conditionNodes) {
    node.conditionNodes.forEach((cond, index) => {
      // 确保有 priorityLevel
      if (cond.priorityLevel === undefined) {
        cond.priorityLevel = index + 1
      }
      
      // 确保有 name
      if (!cond.name) {
        cond.name = '条件' + (index + 1)
      }
      
      // 将 conditionExpression 转换为 conditionList
      if (cond.conditionExpression && !cond.conditionList) {
        cond.conditionList = [{
          key: 'condition_' + index,
          conditionExpression: cond.conditionExpression,
        }]
      }
      
      // 确保 conditionList 是数组
      if (!cond.conditionList) {
        cond.conditionList = []
      }
      
      // 确保有 childNode
      if (!cond.childNode) {
        cond.childNode = {
          key: 'end_' + index,
          name: '结束',
          type: 9
        }
      }
    })
  }
  
  // 递归处理 childNode
  if (node.childNode) {
    convertNodeTypes(node.childNode)
  }
  
  // 递归处理 conditionNodes
  if (node.conditionNodes && Array.isArray(node.conditionNodes)) {
    node.conditionNodes.forEach(convertNodeTypes)
  }
  
  return node
}

const applyAiFlow = (flowData) => {
  try {
    if (!flowData?.nodeConfig) {
      ElMessage.warning('AI 生成的流程数据无效')
      return
    }

    console.log('[FlowAi] 原始数据:', JSON.stringify(flowData, null, 2))

    const payload = {
      nodeConfig: convertNodeTypes(clone(flowData.nodeConfig)),
      flowWidgets: flowData.flowWidgets || formCreateToFlowWidgets(props.formSchema?.rules || []),
      workFlowDef: {
        id: 'wf_' + Date.now().toString(),
        icon: 'approval',
        name: flowData.workFlowDef?.name || 'AI 生成的流程',
        groupId: '',
        cancelable: 1,
        flowAdminIds: [],
        ...(flowData.workFlowDef || {}),
      },
      flowPermission: flowData.flowPermission || { type: 0, flowInitiators: [] },
    }

    console.log('[FlowAi] 处理后的 payload:', JSON.stringify(payload, null, 2))

    // 先更新 FlowStore，再触发重新渲染
    flowStore.setFlowDef(payload)
    console.log('[FlowAi] FlowStore 已更新:', flowStore.flowDefinition)
    
    emit('update:modelValue', payload)
    
    // 等待下一帧再更新 key，确保 store 已更新
    nextTick(() => {
      designerKey.value += 1
      aiVisible.value = false
      ElMessage.success('已应用 AI 生成的流程配置')
    })
  } catch (error) {
    console.error('应用 AI 流程失败:', error)
    ElMessage.error('应用失败: ' + error.message)
  }
}

const flowWidgetsCount = computed(() => flowStore.flowDefinition?.flowWidgets?.length || 0)
</script>

<style scoped lang="scss">
.beeflow-designer {
  display: flex;
  flex-direction: column;
  height: 100%;
  min-height: 520px;
  border: 1px solid #e4e7ed;
  border-radius: 8px;
  overflow: hidden;
  background: #fff;

  &__toolbar {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 16px;
    padding: 12px 16px;
    border-bottom: 1px solid #ebeef5;
    background: #fff;

    .toolbar-info {
      display: flex;
      align-items: baseline;
      gap: 12px;
      min-width: 0;
    }

    .toolbar-title {
      font-size: 15px;
      font-weight: 600;
      color: #303133;
      white-space: nowrap;
    }

    .toolbar-tip {
      font-size: 12px;
      color: #909399;
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
    }

    .toolbar-actions {
      display: flex;
      align-items: center;
      gap: 8px;
      flex-shrink: 0;
    }

    .ai-entry {
      margin-right: 4px;
    }

    .zoom-controls {
      display: flex;
      align-items: center;
      gap: 4px;
      padding: 0 8px;
      border-left: 1px solid #ebeef5;
      border-right: 1px solid #ebeef5;

      .zoom-value {
        font-size: 12px;
        color: #606266;
        min-width: 40px;
        text-align: center;
        user-select: none;
      }
    }
  }

  &__canvas {
    position: relative;
    flex: 1;
    min-height: 460px;
    overflow: auto;
    background-color: #f2f3f5;
    background-image: radial-gradient(#d4d9e1 1px, transparent 1px);
    background-size: 20px 20px;
  }
}
</style>
