<template>
  <div class="ai-config-panel">
    <div class="panel-header">
      <div class="panel-title">
        <el-icon class="ai-icon"><MagicStick /></el-icon>
        <span>AI 模型配置</span>
      </div>
      <el-button size="small" type="primary" @click="openCreate">
        <el-icon><Plus /></el-icon>
        新增配置
      </el-button>
    </div>

    <el-table
      v-loading="loading"
      :data="configs"
      size="small"
      class="config-table"
    >
      <el-table-column prop="provider_display" label="提供商" width="140" />
      <el-table-column prop="model_id" label="模型 ID" min-width="160">
        <template #default="{ row }">
          {{ row.model_id || providerDefaultModel(row.provider) }}
        </template>
      </el-table-column>
      <el-table-column label="API 端点" min-width="220" show-overflow-tooltip>
        <template #default="{ row }">
          <span class="api-base">{{ row.api_base || providerDefaultBase(row.provider) }}</span>
        </template>
      </el-table-column>
      <el-table-column label="API Key" width="110" align="center">
        <template #default="{ row }">
          <el-tooltip
            :content="row.key_env || '环境变量'"
            placement="top"
          >
            <el-tag v-if="row.has_key" size="small" type="success">已配置</el-tag>
            <el-tag v-else size="small" type="info">未配置</el-tag>
          </el-tooltip>
        </template>
      </el-table-column>
      <el-table-column label="启用" width="80" align="center">
        <template #default="{ row }">
          <el-switch
            :model-value="row.is_active"
            @change="(val) => toggleActive(row, val)"
          />
        </template>
      </el-table-column>
      <el-table-column label="操作" width="120" align="center">
        <template #default="{ row }">
          <el-button type="primary" link size="small" @click="openEdit(row)">
            编辑
          </el-button>
          <el-button type="danger" link size="small" @click="removeConfig(row)">
            删除
          </el-button>
        </template>
      </el-table-column>
    </el-table>

    <el-empty
      v-if="!loading && configs.length === 0"
      description="暂无 AI 配置，使用默认配置（小米 MiMo）"
      :image-size="80"
    />

    <!-- 编辑弹窗 -->
    <el-dialog
      v-model="dialogVisible"
      :title="editing ? '编辑 AI 配置' : '新增 AI 配置'"
      width="560px"
      append-to-body
    >
      <el-form :model="form" label-width="110px">
        <el-form-item label="提供商" required>
          <el-select v-model="form.provider" style="width: 100%">
            <el-option
              v-for="p in AI_PROVIDERS"
              :key="p.value"
              :label="p.label"
              :value="p.value"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="模型 ID">
          <el-input
            v-model="form.model_id"
            placeholder="留空使用默认模型"
          />
        </el-form-item>
        <el-form-item label="API 端点">
          <el-input
            v-model="form.api_base"
            placeholder="留空使用默认端点"
          />
        </el-form-item>
        <el-alert
          type="info"
          :closable="false"
          show-icon
          class="key-tip"
          :title="`API Key 通过环境变量 ${envKeyName} 配置，此处无需填写`"
        />
        <el-form-item label="是否启用">
          <el-switch v-model="form.is_active" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="saveConfig">
          保存
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { MagicStick, Plus } from '@element-plus/icons-vue'
import {
  getAiConfigs,
  createAiConfig,
  updateAiConfig,
  deleteAiConfig,
  AI_PROVIDERS
} from '@/api/modules/ai'

const emit = defineEmits(['update'])

const loading = ref(false)
const saving = ref(false)
const configs = ref([])
const dialogVisible = ref(false)
const editing = ref(null)

const form = ref({
  provider: 'xiaomi',
  model_id: '',
  api_base: '',
  is_active: true
})

const envKeyName = computed(() => `AI_${form.value.provider.toUpperCase()}_API_KEY`)

const PROVIDER_DEFAULTS = {
  xiaomi: { model: 'mimo-v2.5', base: 'https://api.xiaomimimo.com/v1/chat/completions' },
  openai: { model: 'gpt-4o', base: 'https://api.openai.com/v1/chat/completions' },
  deepseek: { model: 'deepseek-chat', base: 'https://api.deepseek.com/v1/chat/completions' },
  zhipu: { model: 'glm-4', base: 'https://open.bigmodel.cn/api/paas/v4/chat/completions' },
  qwen: { model: 'qwen-max', base: 'https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions' },
  ollama: { model: 'qwen2.5:7b', base: 'http://host.docker.internal:11434/v1/chat/completions' }
}

const providerDefaultModel = (provider) => PROVIDER_DEFAULTS[provider]?.model || '—'
const providerDefaultBase = (provider) => PROVIDER_DEFAULTS[provider]?.base || '—'

const fetchConfigs = async () => {
  loading.value = true
  try {
    const response = await getAiConfigs({ page_size: 100 })
    const data = response?.data ?? response
    configs.value = Array.isArray(data) ? data : data?.results || []
  } catch (error) {
    console.warn('加载 AI 配置失败:', error)
    configs.value = []
  } finally {
    loading.value = false
  }
}

const openCreate = () => {
  editing.value = null
  form.value = {
    provider: 'xiaomi',
    model_id: '',
    api_base: '',
    is_active: true
  }
  dialogVisible.value = true
}

const openEdit = (row) => {
  editing.value = row
  form.value = {
    provider: row.provider,
    model_id: row.model_id || '',
    api_base: row.api_base || '',
    is_active: row.is_active
  }
  dialogVisible.value = true
}

const saveConfig = async () => {
  if (!form.value.provider) {
    ElMessage.warning('请选择提供商')
    return
  }
  saving.value = true
  try {
    if (editing.value) {
      await updateAiConfig(editing.value.id, form.value)
      ElMessage.success('配置已更新')
    } else {
      await createAiConfig(form.value)
      ElMessage.success('配置已创建')
    }
    dialogVisible.value = false
    await fetchConfigs()
    emit('update')
  } catch (error) {
    console.error('保存 AI 配置失败:', error)
  } finally {
    saving.value = false
  }
}

const toggleActive = async (row, val) => {
  try {
    await updateAiConfig(row.id, { ...row, is_active: val })
    ElMessage.success(val ? '已启用' : '已停用')
    await fetchConfigs()
    emit('update')
  } catch (error) {
    console.error('切换失败:', error)
  }
}

const removeConfig = async (row) => {
  try {
    await ElMessageBox.confirm(`确定删除「${row.provider_display}」配置吗？`, '删除确认', {
      confirmButtonText: '删除',
      cancelButtonText: '取消',
      type: 'warning'
    })
    await deleteAiConfig(row.id)
    ElMessage.success('已删除')
    await fetchConfigs()
    emit('update')
  } catch (error) {
    if (error !== 'cancel') console.error('删除失败:', error)
  }
}

onMounted(fetchConfigs)
</script>

<style scoped lang="scss">
.ai-config-panel {
  .key-tip {
    margin-bottom: 18px;
  }

  .panel-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 16px;

    .panel-title {
      display: flex;
      align-items: center;
      gap: 8px;
      font-size: 15px;
      font-weight: 600;
      color: #303133;

      .ai-icon {
        color: #409eff;
        font-size: 18px;
      }
    }
  }

  .config-table {
    width: 100%;

    .api-base {
      font-size: 12px;
      color: #909399;
      font-family: monospace;
    }
  }
}
</style>
