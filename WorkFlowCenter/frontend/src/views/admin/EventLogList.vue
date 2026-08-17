<template>
  <div class="event-log-list">
    <div class="page-header">
      <div class="page-header-left"><div class="page-header-icon"><el-icon><List /></el-icon></div><div><h1>事件日志</h1><p class="page-header-desc">查看系统事件和操作日志</p></div></div>
      <p>全链路事件记录（流程 / 任务 / 工单），用于审计与排查</p>
    </div>

    <!-- 集成健康度 -->
    <el-card class="health-card" shadow="never" v-loading="statsLoading">
      <template #header><span>集成健康度 · Webhook 投递</span></template>
      <template v-if="stats">
        <div class="health-summary">
          <div class="health-item"><span class="health-num total">{{ stats.summary.total }}</span><span class="health-label">总投递</span></div>
          <div class="health-item"><span class="health-num ok">{{ stats.summary.delivered }}</span><span class="health-label">成功</span></div>
          <div class="health-item"><span class="health-num fail">{{ stats.summary.failed }}</span><span class="health-label">失败</span></div>
          <div class="health-item"><span class="health-num pending">{{ stats.summary.pending }}</span><span class="health-label">重试中</span></div>
        </div>
        <el-table :data="stats.subscriptions" border stripe size="small" class="health-subs">
          <el-table-column prop="name" label="订阅通道" min-width="160" />
          <el-table-column prop="url" label="目标" min-width="220" show-overflow-tooltip />
          <el-table-column label="最近状态" width="100" align="center">
            <template #default="{ row }">
              <el-tag :type="row.last_status === 'delivered' ? 'success' : row.last_status === 'failed' ? 'danger' : 'info'" size="small">
                {{ row.last_status_display || '—' }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column label="投递（总/失败）" width="130" align="center">
            <template #default="{ row }">{{ row.total }} / {{ row.failed }}</template>
          </el-table-column>
          <el-table-column prop="last_time" label="最近投递" width="170" />
        </el-table>
        <div v-if="stats.recent_failed.length" class="health-failed">
          <div class="section-title">最近失败（可重放）</div>
          <div v-for="f in stats.recent_failed" :key="f.id" class="failed-row">
            <span class="failed-info">{{ f.subscription_name }} · {{ f.event_type }}</span>
            <span class="failed-msg">{{ f.last_response }}</span>
            <el-button size="small" type="warning" link @click="retryDelivery(f.id)">重放</el-button>
          </div>
        </div>
        <div v-else class="health-clean">✓ 暂无投递失败</div>
      </template>
    </el-card>

    <!-- 筛选 -->
    <el-card class="filter-card">
      <el-form :inline="true" :model="filterForm">
        <el-form-item label="事件类型">
          <el-select v-model="filterForm.type" placeholder="全部" clearable filterable style="width: 220px">
            <el-option v-for="t in typeOptions" :key="t" :label="eventLabel(t)" :value="t" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="fetchData">查询</el-button>
          <el-button @click="resetFilter">重置</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- 列表 -->
    <el-card>
      <el-table v-loading="loading" :data="tableData" border stripe>
        <el-table-column prop="type" label="事件类型" min-width="150">
          <template #default="{ row }">
            <el-tooltip :content="row.type" placement="top">
              <el-tag effect="plain">{{ eventLabel(row.type) }}</el-tag>
            </el-tooltip>
          </template>
        </el-table-column>
        <el-table-column prop="instance_no" label="流程单号" width="170" show-overflow-tooltip>
          <template #default="{ row }">
            {{ row.instance_no || '-' }}
          </template>
        </el-table-column>
        <el-table-column label="任务" width="120">
          <template #default="{ row }">
            {{ row.task_name || '-' }}
          </template>
        </el-table-column>
        <el-table-column label="工单" width="140" show-overflow-tooltip>
          <template #default="{ row }">
            {{ row.ticket_title || '-' }}
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="时间" width="180" />
        <el-table-column label="操作" width="90" fixed="right">
          <template #default="{ row }">
            <el-button type="primary" link @click="openDetail(row)">详情</el-button>
          </template>
        </el-table-column>
      </el-table>

      <div class="pagination-container">
        <el-pagination
          v-model:current-page="pagination.page"
          v-model:page-size="pagination.pageSize"
          :page-sizes="[10, 20, 50]"
          :total="pagination.total"
          layout="total, sizes, prev, pager, next, jumper"
          @size-change="fetchData"
          @current-change="fetchData"
        />
      </div>
    </el-card>

    <!-- 详情抽屉 -->
    <el-drawer v-model="detailVisible" title="事件详情" size="520px">
      <div v-if="currentEvent" class="event-detail">
        <el-descriptions :column="1" border>
          <el-descriptions-item label="事件类型">
            <el-tooltip :content="currentEvent.type" placement="top">
              <el-tag effect="plain">{{ eventLabel(currentEvent.type) }}</el-tag>
            </el-tooltip>
          </el-descriptions-item>
          <el-descriptions-item label="流程单号">{{ currentEvent.instance_no || '-' }}</el-descriptions-item>
          <el-descriptions-item label="任务">{{ currentEvent.task_name || '-' }}</el-descriptions-item>
          <el-descriptions-item label="工单">{{ currentEvent.ticket_title || '-' }}</el-descriptions-item>
          <el-descriptions-item label="时间">{{ currentEvent.created_at }}</el-descriptions-item>
        </el-descriptions>

        <div class="detail-section">
          <div class="section-title">事件数据（Payload）</div>
          <pre class="json-block">{{ prettyJson(currentEvent.payload) }}</pre>
        </div>
      </div>
    </el-drawer>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { getEvents, getWebhookStats, retryWebhookDelivery } from '@/api/modules/events'
import { eventLabel } from '@/utils/event-labels'

const loading = ref(false)
const statsLoading = ref(false)
const tableData = ref([])
const detailVisible = ref(false)
const currentEvent = ref(null)
const stats = ref(null)

const filterForm = reactive({
  type: ''
})

const pagination = reactive({
  page: 1,
  pageSize: 10,
  total: 0
})

const typeOptions = [
  'process.started', 'process.completed', 'process.terminated',
  'task.created', 'task.completed', 'task.rejected',
  'ticket.created', 'ticket.updated', 'ticket.completed'
]

const fetchData = async () => {
  loading.value = true
  try {
    const params = {
      page: pagination.page,
      page_size: pagination.pageSize,
      ...filterForm
    }
    Object.keys(params).forEach(key => {
      if (params[key] === '' || params[key] === null) {
        delete params[key]
      }
    })
    const response = await getEvents(params)
    const data = response?.data ?? response
    tableData.value = Array.isArray(data) ? data : (data?.results || [])
    pagination.total = data?.count || (Array.isArray(data) ? data.length : 0)
  } catch (error) {
    console.error('获取事件日志失败:', error)
  } finally {
    loading.value = false
  }
}

const resetFilter = () => {
  filterForm.type = ''
  pagination.page = 1
  fetchData()
}

const openDetail = (row) => {
  currentEvent.value = row
  detailVisible.value = true
}

const prettyJson = (obj) => {
  if (!obj || Object.keys(obj).length === 0) return '{}'
  try {
    return JSON.stringify(obj, null, 2)
  } catch (e) {
    return String(obj)
  }
}

const loadStats = async () => {
  statsLoading.value = true
  try {
    const response = await getWebhookStats()
    stats.value = response?.data ?? response
  } catch (e) {
    console.error('获取投递统计失败:', e)
  } finally {
    statsLoading.value = false
  }
}

const retryDelivery = async (id) => {
  try {
    await retryWebhookDelivery(id)
    ElMessage.success('已重新投递')
    loadStats()
  } catch (e) {
    ElMessage.error('重放失败')
  }
}

onMounted(() => {
  fetchData()
  loadStats()
})
</script>

<style scoped lang="scss">
.event-log-list {
  padding: 24px;
  background: var(--ticket-bg, #F7F8FA);
  min-height: 100%;
}

.health-card {
  margin-bottom: 16px;

  .health-summary {
    display: flex;
    gap: 16px;
    margin-bottom: 14px;

    .health-item {
      flex: 1;
      background: #f7f8fa;
      border: 1px solid #e5e6eb;
      border-radius: 10px;
      padding: 12px;
      text-align: center;

      .health-num {
        display: block;
        font-size: 24px;
        font-weight: 700;

        &.total { color: #4e5969; }
        &.ok { color: #00b42a; }
        &.fail { color: #f53f3f; }
        &.pending { color: #ff7d00; }
      }

      .health-label {
        font-size: 12px;
        color: #86909c;
      }
    }
  }

  .health-subs {
    margin-bottom: 14px;
  }

  .section-title {
    font-size: 13px;
    font-weight: 600;
    color: #4e5969;
    margin-bottom: 8px;
  }

  .failed-row {
    display: flex;
    align-items: center;
    gap: 10px;
    padding: 6px 0;
    border-bottom: 1px dashed #f2f3f5;

    .failed-info {
      font-size: 12.5px;
      color: #4e5969;
      flex-shrink: 0;
    }

    .failed-msg {
      flex: 1;
      font-size: 12px;
      color: #86909c;
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
    }
  }

  .health-clean {
    font-size: 13px;
    color: #00b42a;
  }
}

.page-header {
  margin-bottom: 20px;

  h2 {
    margin: 0 0 4px;
    color: #303133;
    font-size: 20px;
  }

  p {
    margin: 0;
    font-size: 13px;
    color: #909399;
  }
}

.filter-card {
  margin-bottom: 16px;
}

.pagination-container {
  display: flex;
  justify-content: flex-end;
  margin-top: 20px;
}

.event-detail {
  .detail-section {
    margin-top: 20px;

    .section-title {
      font-size: 14px;
      font-weight: 600;
      color: #303133;
      margin-bottom: 8px;
    }

    .json-block {
      background: #f5f7fa;
      border: 1px solid #ebeef5;
      border-radius: 8px;
      padding: 12px;
      font-size: 12px;
      font-family: monospace;
      max-height: 400px;
      overflow: auto;
      white-space: pre-wrap;
      word-break: break-all;
    }
  }
}
</style>
