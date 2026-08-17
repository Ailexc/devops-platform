<template>
  <div class="preview-page">
    <div class="preview-header">
      <div>
        <h2>流程设计器预览（方案 B 集成 Demo）</h2>
        <p class="preview-sub">左侧为示例表单（form-create），右侧为 Beeflow 流程设计器；办理节点支持「任务绑定」</p>
      </div>
      <el-button size="small" @click="exportFlow">导出流程 JSON</el-button>
    </div>

    <el-row :gutter="16" class="preview-body">
      <el-col :xs="24" :md="8" :lg="7">
        <el-card class="preview-form-card" shadow="never">
          <template #header>
            <span>示例表单 schema</span>
          </template>
          <pre class="schema-view">{{ JSON.stringify(sampleForm, null, 2) }}</pre>
        </el-card>
      </el-col>
      <el-col :xs="24" :md="16" :lg="17">
        <ProcessFlowDesigner v-model="flowJson" :form-schema="sampleForm" />
      </el-col>
    </el-row>

    <el-card v-if="flowJson" class="preview-output" shadow="never">
      <template #header>
        <span>流程 JSON（保存结果）</span>
      </template>
      <pre class="schema-view">{{ JSON.stringify(flowJson, null, 2) }}</pre>
    </el-card>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import ProcessFlowDesigner from '@/components/FlowDesigner/ProcessFlowDesigner.vue'

// 模拟 form-create 表单 schema（与 FormBuilder 输出结构一致）
const sampleForm = {
  rules: [
    {
      type: 'input',
      field: 'title',
      title: '申请标题',
      value: '',
      validate: [{ required: true, message: '请输入标题' }],
    },
    {
      type: 'textarea',
      field: 'reason',
      title: '申请说明',
      value: '',
    },
    {
      type: 'inputNumber',
      field: 'amount',
      title: '金额',
      value: 0,
      props: { min: 0 },
    },
    {
      type: 'select',
      field: 'type',
      title: '申请类型',
      value: 'leave',
      options: [
        { label: '请假', value: 'leave' },
        { label: '报销', value: 'expense' },
        { label: '采购', value: 'purchase' },
      ],
    },
    {
      type: 'datePicker',
      field: 'start_date',
      title: '开始日期',
      value: '',
    },
    {
      type: 'checkbox',
      field: 'tags',
      title: '标签',
      value: [],
      options: [
        { label: '加急', value: 'urgent' },
        { label: '跨部门', value: 'cross' },
      ],
    },
  ],
  options: {},
}

const flowJson = ref(null)

function exportFlow() {
  if (!flowJson.value) return
  const blob = new Blob([JSON.stringify(flowJson.value, null, 2)], { type: 'application/json' })
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = 'flow-design.json'
  link.click()
  URL.revokeObjectURL(url)
}
</script>

<style scoped lang="scss">
.preview-page {
  min-height: 100vh;
  padding: 24px;
  background: #f5f7fa;
}

.preview-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
  margin-bottom: 16px;

  h2 {
    margin: 0 0 6px;
    font-size: 20px;
    color: #303133;
  }

  .preview-sub {
    margin: 0;
    font-size: 13px;
    color: #909399;
  }
}

.preview-body {
  align-items: stretch;
}

.preview-form-card,
.preview-output {
  border-radius: 8px;
}

.preview-form-card :deep(.el-card__body) {
  padding: 12px;
}

.schema-view {
  margin: 0;
  font-size: 12px;
  line-height: 1.6;
  color: #475569;
  white-space: pre-wrap;
  word-break: break-all;
}

.preview-output {
  margin-top: 16px;
}
</style>
