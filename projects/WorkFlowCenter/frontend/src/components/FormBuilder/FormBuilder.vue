<template>
  <div class="form-builder-wrapper">
    <div class="form-builder-toolbar">
      <div class="toolbar-left">
        <span class="toolbar-title">表单设计</span>
      </div>
      <div class="toolbar-right">
        <el-button-group>
          <el-button @click="openAiPanel" size="small" type="primary" plain class="ai-entry">
            <el-icon><MagicStick /></el-icon>
            AI 智能助理
          </el-button>
          <el-button @click="getJson" size="small">
            <el-icon><Document /></el-icon>
            获取 JSON
          </el-button>
          <el-button @click="setJson" size="small">
            <el-icon><Upload /></el-icon>
            导入 JSON
          </el-button>
          <el-button @click="clearForm" size="small" type="danger" plain>
            <el-icon><Delete /></el-icon>
            清空
          </el-button>
        </el-button-group>
      </div>
    </div>
    <fc-designer ref="designerRef" :config="designerConfig" />

    <!-- AI 表单生成 -->
    <el-drawer
      v-model="aiVisible"
      title="AI 智能助理（MiMo 驱动）"
      size="520px"
      append-to-body
      destroy-on-close
    >
      <AiPromptPanel
        :current-schema="props.modelValue"
        @apply="applyAiSchema"
      />
    </el-drawer>
  </div>
</template>

<script setup>
import { ref, watch, onMounted } from 'vue'
import { Document, Upload, Delete, MagicStick } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import AiPromptPanel from '@/components/form/AiPromptPanel.vue'

const props = defineProps({
  modelValue: {
    type: Object,
    default: () => ({ rules: [], options: {} })
  }
})

const emit = defineEmits(['update:modelValue'])

const designerRef = ref(null)

const designerConfig = {
  showDeviceList: false,
  showJsonPreview: false,
  showImportJson: false,
  showExportJson: false,
  showClear: false,
  // 禁用 form-create 内置的第三方 AI 助理（需要 form-create.com 付费 Key，
  // 且会把表单内容发送到其云端）；统一使用上方「AI 智能助理」按钮（走本项目 MiMo 配置）
  showAi: false,
}

onMounted(() => {
  if (props.modelValue?.rules?.length > 0) {
    try {
      designerRef.value?.setRule(props.modelValue.rules || [])
      if (props.modelValue.options) {
        designerRef.value?.setOption(props.modelValue.options)
      }
    } catch (e) {
      console.warn('导入表单规则失败:', e)
    }
  }
})

watch(
  () => props.modelValue,
  (newVal) => {
    if (newVal?.rules?.length > 0 && designerRef.value) {
      try {
        designerRef.value.setRule(newVal.rules)
        if (newVal.options) {
          designerRef.value.setOption(newVal.options)
        }
      } catch (e) {}
    }
  },
  { deep: true }
)

const getJson = () => {
  if (!designerRef.value) return
  const rules = designerRef.value.getRule()
  const options = designerRef.value.getOption()
  const formSchema = { rules, options }
  emit('update:modelValue', formSchema)
  ElMessage.success('表单规则已保存')
  console.log('Form Schema:', JSON.stringify(formSchema, null, 2))
}

const setJson = () => {
  ElMessageBox.prompt('请输入 form-create 规则 JSON', '导入表单', {
    confirmButtonText: '导入',
    cancelButtonText: '取消',
    inputType: 'textarea',
    inputPlaceholder: '粘贴 JSON...',
  }).then(({ value }) => {
    try {
      const data = JSON.parse(value)
      if (data.rules) {
        designerRef.value?.setRule(data.rules)
        if (data.options) designerRef.value?.setOption(data.options)
      } else if (Array.isArray(data)) {
        designerRef.value?.setRule(data)
      }
      emit('update:modelValue', data.rules ? data : { rules: data, options: {} })
      ElMessage.success('导入成功')
    } catch (e) {
      ElMessage.error('JSON 格式错误: ' + e.message)
    }
  }).catch(() => {})
}

const clearForm = () => {
  ElMessageBox.confirm('确定要清空所有表单配置吗？', '确认', {
    confirmButtonText: '确定',
    cancelButtonText: '取消',
    type: 'warning',
  }).then(() => {
    designerRef.value?.setRule([])
    emit('update:modelValue', { rules: [], options: {} })
    ElMessage.success('已清空')
  }).catch(() => {})
}

// ================= AI 表单生成 =================
const aiVisible = ref(false)

const openAiPanel = () => {
  aiVisible.value = true
}

// 将 AI 生成的 schema 规范化为 form-create 规则
const normalizeAiRule = (rule) => {
  const r = { ...rule }
  // 类型映射：form-create 组件名称
  const typeMap = {
    money: 'inputNumber',
    'input-number': 'inputNumber',
    text: 'input',
    email: 'input',
    number: 'inputNumber'
  }
  if (typeMap[r.type]) {
    r.type = typeMap[r.type]
  }
  // 单选/多选选项转换为 form-create 格式（支持字符串数组和对象数组）
  if (r.options && typeof r.options === 'string') {
    try {
      r.options = JSON.parse(r.options)
    } catch (e) {
      r.options = []
    }
  }
  // inputNumber 增加数字校验
  if (r.type === 'inputNumber' && !r.props) {
    r.props = { precision: 2, controls: true }
  }
  return r
}

const applyAiSchema = (schema) => {
  try {
    const rules = (schema?.rules || []).map(normalizeAiRule)
    if (rules.length === 0) {
      ElMessage.warning('AI 生成的表单为空')
      return
    }
    designerRef.value?.setRule(rules)
    if (schema?.options) {
      designerRef.value?.setOption(schema.options)
    }
    emit('update:modelValue', {
      rules,
      options: schema?.options || { form: { labelWidth: '120px' } }
    })
    aiVisible.value = false
    ElMessage.success(`已应用 ${rules.length} 个表单字段`)
  } catch (error) {
    console.error('应用 AI 表单失败:', error)
    ElMessage.error('应用 AI 表单失败，请检查生成结果')
  }
}
</script>

<style scoped>
.form-builder-wrapper {
  border: 1px solid #e4e7ed;
  border-radius: 8px;
  overflow: hidden;
  background: #fff;
}

.form-builder-toolbar {
  padding: 10px 16px;
  background: #f5f7fa;
  border-bottom: 1px solid #e4e7ed;
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.toolbar-left .toolbar-title {
  font-size: 14px;
  font-weight: 600;
  color: #303133;
}

.toolbar-right {
  display: flex;
  align-items: center;
}

.ai-entry {
  margin-right: 8px;
}

.form-builder-wrapper :deep(.fc-designer) {
  min-height: 500px;
}

.form-builder-wrapper :deep(.fc-designer .el-aside) {
  width: 280px !important;
}
</style>
