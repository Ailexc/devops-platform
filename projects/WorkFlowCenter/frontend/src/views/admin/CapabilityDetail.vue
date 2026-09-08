<template>
  <div class="capability-detail">
    <div class="page-header">
      <div class="page-header-left">
        <div class="page-header-back" @click="$router.push('/admin/capabilities')">
          <el-icon><ArrowLeft /></el-icon>
        </div>
        <div>
          <h1>{{ capability?.name || '能力详情' }}</h1>
          <p class="page-header-desc">查看能力配置和执行记录</p>
        </div>
      </div>
      <el-tag :type="capability?.is_active ? 'success' : 'info'" size="large">
        {{ capability?.is_active ? '启用' : '停用' }}
      </el-tag>
    </div>

    <el-row :gutter="20" v-loading="loading">
      <!-- 左侧：基本信息 + 输入调试 -->
      <el-col :xs="24" :md="14">
        <el-card class="info-card">
          <template #header><span>基本信息</span></template>
          <el-descriptions :column="2" border>
            <el-descriptions-item label="能力编码">
              <code>{{ capability?.code }}</code>
            </el-descriptions-item>
            <el-descriptions-item label="执行模式">
              <el-tag size="small" effect="plain">{{ capability?.execute_mode === 'sync' ? '同步' : '异步' }}</el-tag>
            </el-descriptions-item>
            <el-descriptions-item label="端点 URL" :span="2">
              {{ capability?.endpoint || '未配置（使用 Mock 执行）' }}
            </el-descriptions-item>
            <el-descriptions-item label="描述" :span="2">
              {{ capability?.description || '-' }}
            </el-descriptions-item>
          </el-descriptions>
        </el-card>

        <el-card class="debug-card">
          <template #header>
            <div class="card-header">
              <span>调试执行</span>
              <el-tag size="small" :type="testMode === 'mock' ? 'warning' : 'success'" effect="plain">
                {{ testMode === 'mock' ? 'Mock 模式' : 'HTTP 模式' }}
              </el-tag>
            </div>
          </template>

          <el-form :model="testForm" label-width="0" class="test-form">
            <div v-if="inputFields.length === 0" class="empty-schema">
              该能力未定义输入参数，可直接执行
            </div>
            <div v-for="field in inputFields" :key="field.name" class="input-field">
              <div class="field-label">
                {{ field.title || field.name }}
                <el-tag v-if="field.required" size="small" type="danger" effect="plain">必填</el-tag>
              </div>
              <el-input-number
                v-if="field.type === 'integer' || field.type === 'number'"
                v-model="testForm[field.name]"
                :controls="false"
                style="width: 100%"
              />
              <el-select
                v-else-if="field.enum"
                v-model="testForm[field.name]"
                placeholder="请选择"
                style="width: 100%"
              >
                <el-option v-for="opt in field.enum" :key="opt" :label="opt" :value="opt" />
              </el-select>
              <el-checkbox-group
                v-else-if="field.type === 'array'"
                v-model="testForm[field.name]"
              >
                <el-checkbox v-for="opt in field.items?.enum || []" :key="opt" :label="opt" />
              </el-checkbox-group>
              <el-input
                v-else
                v-model="testForm[field.name]"
                :placeholder="field.placeholder || `请输入${field.title || field.name}`"
              />
            </div>

            <div class="debug-actions">
              <el-button type="primary" :loading="testing" @click="runTest">
                <el-icon><Cpu /></el-icon>
                执行测试
              </el-button>
            </div>
          </el-form>

          <div v-if="testResult" class="test-result">
            <div class="result-title" :class="{ error: !testResult.success }">
              {{ testResult.success ? '执行成功' : '执行失败' }}
            </div>
            <pre v-if="testResult.success" class="result-json">{{ prettyJson(testResult.output) }}</pre>
            <pre v-else class="result-json error-block">{{ testResult.error }}</pre>
          </div>
        </el-card>
      </el-col>

      <!-- 右侧：输入/输出 Schema -->
      <el-col :xs="24" :md="10">
        <el-card class="schema-card">
          <template #header><span>输入 Schema</span></template>
          <pre class="schema-json">{{ prettyJson(capability?.input_schema) }}</pre>
        </el-card>

        <el-card class="schema-card">
          <template #header><span>输出 Schema</span></template>
          <pre class="schema-json">{{ prettyJson(capability?.output_schema) }}</pre>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import { ArrowLeft, Cpu } from '@element-plus/icons-vue'
import { getCapability, testCapability } from '@/api/modules/capability'

const route = useRoute()
const loading = ref(false)
const testing = ref(false)
const capability = ref(null)
const testForm = ref({})
const testResult = ref(null)
const testMode = ref('mock')

// 从 input_schema 提取字段
const inputFields = computed(() => {
  const schema = capability.value?.input_schema || {}
  const properties = schema.properties || {}
  const required = schema.required || []
  return Object.entries(properties).map(([name, prop]) => ({
    name,
    ...prop,
    required: required.includes(name)
  }))
})

const fetchDetail = async () => {
  loading.value = true
  try {
    const response = await getCapability(route.params.id)
    capability.value = response?.data ?? response
    testMode.value = capability.value?.endpoint ? 'http' : 'mock'
    // 初始化调试表单默认值
    const defaults = {}
    inputFields.value.forEach(f => {
      if (f.type === 'array') defaults[f.name] = []
      else if (f.type === 'integer' || f.type === 'number') defaults[f.name] = undefined
      else defaults[f.name] = ''
    })
    testForm.value = defaults
  } catch (error) {
    console.error('获取能力详情失败:', error)
    ElMessage.error('获取能力详情失败')
  } finally {
    loading.value = false
  }
}

const runTest = async () => {
  testing.value = true
  testResult.value = null
  try {
    // 过滤空值
    const payload = {}
    Object.entries(testForm.value).forEach(([k, v]) => {
      if (v !== '' && v !== undefined && v !== null) {
        payload[k] = v
      }
    })
    const response = await testCapability(route.params.id, payload)
    const data = response?.data ?? response
    if (data?.success) {
      testResult.value = { success: true, output: data.output }
    } else {
      testResult.value = { success: false, error: data?.error || '执行失败' }
    }
  } catch (error) {
    const detail = error?.response?.data?.message || '测试执行失败'
    testResult.value = { success: false, error: detail }
  } finally {
    testing.value = false
  }
}

const prettyJson = (obj) => {
  if (!obj || Object.keys(obj).length === 0) return '{}'
  try {
    return JSON.stringify(obj, null, 2)
  } catch (e) {
    return String(obj)
  }
}

onMounted(() => {
  fetchDetail()
})
</script>

<style scoped lang="scss">
.capability-detail {
  padding: 24px;
  background: var(--ticket-bg, #F7F8FA);
  min-height: 100%;
  max-width: 1280px;
  margin: 0 auto;
}

.page-header {
  display: flex;
  align-items: center;
  gap: 16px;
  margin-bottom: 20px;

  h2 {
    margin: 0;
    color: #303133;
    font-size: 20px;
    flex: 1;
  }
}

.info-card {
  margin-bottom: 20px;

  code {
    background: #f5f7fa;
    padding: 2px 6px;
    border-radius: 4px;
    font-size: 12px;
    color: #409eff;
  }
}

.debug-card {
  .card-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
  }

  .test-form {
    .empty-schema {
      color: #909399;
      font-size: 13px;
      padding: 12px 0;
    }

    .input-field {
      margin-bottom: 16px;

      .field-label {
        font-size: 13px;
        font-weight: 500;
        color: #303133;
        margin-bottom: 6px;
        display: flex;
        align-items: center;
        gap: 8px;
      }
    }

    .debug-actions {
      margin-top: 20px;
    }
  }

  .test-result {
    margin-top: 20px;
    border-top: 1px solid #ebeef5;
    padding-top: 16px;

    .result-title {
      font-size: 14px;
      font-weight: 600;
      color: #67c23a;
      margin-bottom: 8px;

      &.error {
        color: #f56c6c;
      }
    }

    .result-json {
      background: #f5f7fa;
      border: 1px solid #ebeef5;
      border-radius: 8px;
      padding: 12px;
      font-size: 12px;
      font-family: monospace;
      max-height: 300px;
      overflow: auto;
      white-space: pre-wrap;
      word-break: break-all;

      &.error-block {
        background: #fef0f0;
        border-color: #fde2e2;
        color: #f56c6c;
      }
    }
  }
}

.schema-card {
  margin-bottom: 20px;

  .schema-json {
    background: #f5f7fa;
    border-radius: 6px;
    padding: 12px;
    font-size: 12px;
    font-family: monospace;
    max-height: 320px;
    overflow: auto;
    white-space: pre-wrap;
    word-break: break-all;
    margin: 0;
  }
}
</style>
