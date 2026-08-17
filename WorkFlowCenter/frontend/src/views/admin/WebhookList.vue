<template>
  <div class="webhook-list">
    <div class="page-header">
      <div class="page-header-left"><div class="page-header-icon"><el-icon><Promotion /></el-icon></div><div><h1>Webhook 订阅</h1><p class="page-header-desc">配置事件推送和回调通知</p></div></div>
      <p>配置外部系统回调，接收流程事件通知</p>
      <el-button type="primary" @click="openCreate">
        <el-icon><Plus /></el-icon>
        新建订阅
      </el-button>
    </div>

    <!-- 订阅列表 -->
    <el-card>
      <!-- 真实业务场景说明 -->
      <div class="scene-card">
        <div class="scene-card__title"><el-icon><Promotion /></el-icon> 真实业务场景</div>
        <p class="scene-card__desc">
          任务中心通常是<strong>独立的外部系统平台</strong>（如流水线 / 作业平台 / Jenkins）。
          本系统通过 <strong>Webhook 订阅</strong> 接收其消息推送（任务状态变更、执行日志等），
          实现异步任务的进度跟踪与状态回写：
        </p>
        <div class="scene-flow">
          <span class="scene-flow__node">流程引擎</span>
          <span class="scene-flow__arrow">→</span>
          <span class="scene-flow__node">提交异步任务</span>
          <span class="scene-flow__arrow">→</span>
          <span class="scene-flow__node">外部任务中心执行</span>
          <span class="scene-flow__arrow">→</span>
          <span class="scene-flow__node">Webhook 推送状态</span>
          <span class="scene-flow__arrow">→</span>
          <span class="scene-flow__node">本系统订阅回调 · 更新节点状态</span>
        </div>
        <p class="scene-card__hint">
          Demo 中模拟了这一机制：下方订阅即代表「外部任务中心」向本系统推送任务状态，流程引擎按推送结果推进节点。
        </p>
      </div>

      <!-- 即将支持的功能提示 -->
      <el-alert
        title="Webhook 签名验证"
        description="HMAC 签名验证功能即将上线，届时回调请求将携带 X-Webhook-Signature 头部，用于验证请求来源的合法性。当前版本暂不支持。"
        type="info"
        show-icon
        :closable="true"
        style="margin-bottom: 16px;"
      />
      <el-table v-loading="loading" :data="tableData" border stripe>
        <el-table-column prop="name" label="订阅名称" min-width="140" />
        <el-table-column prop="url" label="回调 URL" min-width="240" show-overflow-tooltip />
        <el-table-column label="订阅事件" min-width="180">
          <template #default="{ row }">
            <el-tag
              v-for="evt in row.events"
              :key="evt"
              size="small"
              effect="plain"
              class="event-tag"
            >
              {{ evt }}
            </el-tag>
            <span v-if="!row.events?.length">-</span>
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
        <el-table-column label="投递记录" width="100" align="center">
          <template #default="{ row }">
            <el-button type="primary" link @click="viewDeliveries(row)">查看</el-button>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="创建时间" width="180" />
        <el-table-column label="操作" width="140" fixed="right">
          <template #default="{ row }">
            <el-button type="primary" link @click="openEdit(row)">编辑</el-button>
            <el-button type="danger" link @click="remove(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>

      <div class="pagination-container">
        <el-pagination
          v-model:current-page="pagination.page"
          v-model:page-size="pagination.pageSize"
          :total="pagination.total"
          layout="total, prev, pager, next"
          @current-change="fetchData"
        />
      </div>
    </el-card>

    <!-- 创建/编辑 -->
    <el-dialog v-model="dialogVisible" :title="editing ? '编辑订阅' : '新建订阅'" width="560px">
      <el-form :model="form" label-width="100px">
        <el-form-item label="订阅名称" required>
          <el-input v-model="form.name" placeholder="如：通知外部审批系统" />
        </el-form-item>
        <el-form-item label="回调 URL" required>
          <el-input v-model="form.url" placeholder="https://example.com/hook" />
        </el-form-item>
        <el-form-item label="订阅事件">
          <el-select
            v-model="form.events"
            multiple
            filterable
            allow-create
            default-first-option
            style="width: 100%"
            placeholder="选择或输入事件类型"
          >
            <el-option
              v-for="e in eventOptions"
              :key="e"
              :label="e"
              :value="e"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="签名密钥">
          <el-input v-model="form.secret" placeholder="用于校验请求来源（可选）" />
        </el-form-item>
        <el-form-item label="启用">
          <el-switch v-model="form.is_active" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="save">保存</el-button>
      </template>
    </el-dialog>

    <!-- 投递记录抽屉 -->
    <el-drawer v-model="deliveryVisible" title="投递记录" size="640px">
      <div v-if="currentSubscription" class="delivery-header">
        <span class="delivery-name">{{ currentSubscription.name }}</span>
        <span class="delivery-url">{{ currentSubscription.url }}</span>
      </div>
      <el-table :data="deliveries" size="small" v-loading="deliveryLoading" border>
        <el-table-column prop="id" label="ID" width="60" />
        <el-table-column label="事件" min-width="150">
          <template #default="{ row }">
            {{ row.event_type }}
          </template>
        </el-table-column>
        <el-table-column label="状态" width="90" align="center">
          <template #default="{ row }">
            <el-tag :type="deliveryStatusType(row.status)" size="small">
              {{ deliveryStatusLabel(row.status) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="attempt" label="次数" width="60" align="center" />
        <el-table-column prop="created_at" label="时间" width="170" />
        <el-table-column label="响应" min-width="120">
          <template #default="{ row }">
            <el-tooltip :content="row.last_response || '-'" placement="top">
              <span class="response-text">{{ (row.last_response || '-').substring(0, 30) }}</span>
            </el-tooltip>
          </template>
        </el-table-column>
      </el-table>
    </el-drawer>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Promotion } from '@element-plus/icons-vue'
import {
  getWebhooks, createWebhook, updateWebhook, deleteWebhook, getWebhookDeliveries
} from '@/api/modules/events'

const loading = ref(false)
const saving = ref(false)
const tableData = ref([])
const dialogVisible = ref(false)
const editing = ref(null)
const deliveryVisible = ref(false)
const deliveryLoading = ref(false)
const deliveries = ref([])
const currentSubscription = ref(null)

const filterForm = reactive({})

const pagination = reactive({
  page: 1,
  pageSize: 10,
  total: 0
})

const form = reactive({
  name: '',
  url: '',
  events: [],
  secret: '',
  is_active: true
})

const eventOptions = [
  'process.started', 'process.completed', 'process.terminated',
  'task.created', 'task.completed', 'task.claimed',
  'ticket.created', 'ticket.updated', 'ticket.completed'
]

const fetchData = async () => {
  loading.value = true
  try {
    const response = await getWebhooks({ page: pagination.page, page_size: pagination.pageSize })
    const data = response?.data ?? response
    tableData.value = Array.isArray(data) ? data : (data?.results || [])
    pagination.total = data?.count || (Array.isArray(data) ? data.length : 0)
  } catch (error) {
    console.error('获取 Webhook 列表失败:', error)
  } finally {
    loading.value = false
  }
}

const openCreate = () => {
  editing.value = null
  Object.assign(form, { name: '', url: '', events: [], secret: '', is_active: true })
  dialogVisible.value = true
}

const openEdit = (row) => {
  editing.value = row
  Object.assign(form, {
    name: row.name,
    url: row.url,
    events: row.events || [],
    secret: row.secret || '',
    is_active: row.is_active
  })
  dialogVisible.value = true
}

const save = async () => {
  if (!form.name || !form.url) {
    ElMessage.warning('请填写订阅名称和回调 URL')
    return
  }
  saving.value = true
  try {
    if (editing.value) {
      await updateWebhook(editing.value.id, form)
      ElMessage.success('订阅已更新')
    } else {
      await createWebhook(form)
      ElMessage.success('订阅已创建')
    }
    dialogVisible.value = false
    fetchData()
  } catch (error) {
    console.error('保存失败:', error)
  } finally {
    saving.value = false
  }
}

const toggleActive = async (row, val) => {
  try {
    await updateWebhook(row.id, { ...row, is_active: val })
    ElMessage.success(val ? '已启用' : '已停用')
  } catch (error) {
    console.error('切换失败:', error)
  }
}

const remove = async (row) => {
  try {
    await ElMessageBox.confirm(`确定删除订阅「${row.name}」吗？`, '删除确认', {
      confirmButtonText: '删除',
      cancelButtonText: '取消',
      type: 'warning'
    })
    await deleteWebhook(row.id)
    ElMessage.success('已删除')
    fetchData()
  } catch (error) {
    if (error !== 'cancel') console.error('删除失败:', error)
  }
}

const viewDeliveries = async (row) => {
  currentSubscription.value = row
  deliveryVisible.value = true
  deliveryLoading.value = true
  try {
    const response = await getWebhookDeliveries({ subscription: row.id, page_size: 50 })
    const data = response?.data ?? response
    deliveries.value = Array.isArray(data) ? data : (data?.results || [])
  } catch (error) {
    console.error('获取投递记录失败:', error)
    deliveries.value = []
  } finally {
    deliveryLoading.value = false
  }
}

const deliveryStatusType = (status) => {
  const types = { pending: 'info', delivered: 'success', failed: 'danger' }
  return types[status] || 'info'
}

const deliveryStatusLabel = (status) => {
  const labels = { pending: '待投递', delivered: '已投递', failed: '失败' }
  return labels[status] || status
}

onMounted(() => {
  fetchData()
})
</script>

<style scoped lang="scss">
.webhook-list {
  padding: 24px;
  background: var(--ticket-bg, #F7F8FA);
  min-height: 100%;
}

.page-header {
  margin-bottom: 20px;

  h2 {
    margin: 0 0 4px;
    color: #303133;
    font-size: 20px;
  }

  p {
    margin: 0 0 12px;
    font-size: 13px;
    color: #909399;
  }
}

.event-tag {
  margin-right: 4px;
  margin-bottom: 2px;
}

.scene-card {
  background: linear-gradient(135deg, #e8f3ff 0%, #f0f7ff 100%);
  border: 1px solid #a0cfff;
  border-radius: 10px;
  padding: 16px 18px;
  margin-bottom: 16px;

  .scene-card__title {
    display: flex;
    align-items: center;
    gap: 6px;
    font-size: 14px;
    font-weight: 600;
    color: #165dff;
    margin-bottom: 8px;
  }

  .scene-card__desc {
    margin: 0 0 10px;
    font-size: 13px;
    color: #4e5969;
    line-height: 1.7;

    strong {
      color: #165dff;
    }
  }

  .scene-flow {
    display: flex;
    align-items: center;
    gap: 8px;
    flex-wrap: wrap;
    margin-bottom: 10px;

    .scene-flow__node {
      font-size: 12px;
      color: #1d2129;
      background: #fff;
      border: 1px solid #a0cfff;
      border-radius: 6px;
      padding: 4px 10px;
      font-weight: 500;
    }

    .scene-flow__arrow {
      color: #86909c;
      font-size: 14px;
    }
  }

  .scene-card__hint {
    margin: 0;
    font-size: 12px;
    color: #86909c;
  }
}

.pagination-container {
  display: flex;
  justify-content: flex-end;
  margin-top: 20px;
}

.delivery-header {
  margin-bottom: 16px;

  .delivery-name {
    font-size: 15px;
    font-weight: 600;
    color: #303133;
    margin-right: 12px;
  }

  .delivery-url {
    font-size: 12px;
    color: #909399;
  }
}

.response-text {
  font-size: 12px;
  color: #606266;
  cursor: default;
}
</style>
