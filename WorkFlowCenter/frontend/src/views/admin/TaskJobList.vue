<template>
  <div class="task-job-list">
    <div class="page-header">
      <div class="page-header-left"><div class="page-header-icon"><el-icon><DataAnalysis /></el-icon></div><div><h1>任务中心</h1><p class="page-header-desc">管理定时任务和异步作业</p></div></div>
      <p>查看所有能力任务的执行记录、输入输出与错误信息</p>
    </div>

    <!-- 统计卡片 -->
    <el-row :gutter="16" class="stats-row">
      <el-col :xs="12" :md="6">
        <el-card shadow="hover" class="stat-card">
          <div class="stat-value">{{ stats.total }}</div>
          <div class="stat-label">执行总数</div>
        </el-card>
      </el-col>
      <el-col :xs="12" :md="6">
        <el-card shadow="hover" class="stat-card success">
          <div class="stat-value">{{ stats.succeeded }}</div>
          <div class="stat-label">成功</div>
        </el-card>
      </el-col>
      <el-col :xs="12" :md="6">
        <el-card shadow="hover" class="stat-card warning">
          <div class="stat-value">{{ stats.running }}</div>
          <div class="stat-label">执行中</div>
        </el-card>
      </el-col>
      <el-col :xs="12" :md="6">
        <el-card shadow="hover" class="stat-card danger">
          <div class="stat-value">{{ stats.failed }}</div>
          <div class="stat-label">失败</div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 筛选 -->
    <el-card class="filter-card">
      <el-form :inline="true" :model="filterForm">
        <el-form-item label="状态">
          <el-select v-model="filterForm.status" placeholder="全部" clearable>
            <el-option label="排队中" value="queued" />
            <el-option label="执行中" value="running" />
            <el-option label="成功" value="succeeded" />
            <el-option label="失败" value="failed" />
          </el-select>
        </el-form-item>
        <el-form-item label="能力">
          <el-select v-model="filterForm.capability" placeholder="全部" clearable>
            <el-option v-for="c in capabilities" :key="c.id" :label="c.name" :value="c.id" />
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
        <el-table-column prop="job_id" label="Job ID" width="200" show-overflow-tooltip>
          <template #default="{ row }">
            <el-button type="primary" link @click="openDetail(row)">{{ row.job_id }}</el-button>
          </template>
        </el-table-column>
        <el-table-column prop="capability_name" label="能力" width="140">
          <template #default="{ row }">
            <el-tag effect="plain">{{ row.capability_name }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="instance_no" label="流程单号" width="160" show-overflow-tooltip />
        <el-table-column prop="status_display" label="状态" width="100" align="center">
          <template #default="{ row }">
            <el-tag :type="getStatusType(row.status)">{{ row.status_display }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="耗时" width="90" align="center">
          <template #default="{ row }">
            <span v-if="row.started_at && row.completed_at">{{ duration(row.started_at, row.completed_at) }}</span>
            <span v-else>-</span>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="创建时间" width="180" />
        <el-table-column label="操作" width="130" fixed="right">
          <template #default="{ row }">
            <el-button type="primary" link @click="openDetail(row)">详情</el-button>
            <el-button
              v-if="row.status === 'failed'"
              type="warning"
              link
              @click="retryJob(row)"
            >
              重试
            </el-button>
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
    <el-drawer v-model="detailVisible" title="任务执行详情" size="560px">
      <div v-if="currentJob" class="job-detail">
        <el-descriptions :column="1" border>
          <el-descriptions-item label="Job ID">{{ currentJob.job_id }}</el-descriptions-item>
          <el-descriptions-item label="能力">
            {{ currentJob.capability_name }}（{{ currentJob.capability_code }}）
          </el-descriptions-item>
          <el-descriptions-item label="状态">
            <el-tag :type="getStatusType(currentJob.status)">{{ currentJob.status_display }}</el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="执行模式">
            {{ currentJob.sync ? '同步' : '异步' }}
          </el-descriptions-item>
          <el-descriptions-item label="开始时间">{{ currentJob.started_at || '-' }}</el-descriptions-item>
          <el-descriptions-item label="完成时间">{{ currentJob.completed_at || '-' }}</el-descriptions-item>
        </el-descriptions>

        <div class="detail-section">
          <div class="section-title">输入数据</div>
          <pre class="json-block">{{ prettyJson(currentJob.input_data) }}</pre>
        </div>

        <div class="detail-section">
          <div class="section-title">输出数据</div>
          <pre class="json-block">{{ prettyJson(currentJob.output_data) }}</pre>
        </div>

        <div v-if="currentJob.error_message" class="detail-section">
          <div class="section-title error">错误信息</div>
          <pre class="json-block error-block">{{ currentJob.error_message }}</pre>
        </div>
      </div>
    </el-drawer>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  getTaskJobs, getTaskJobStats, getCapabilities, executeTaskJob
} from '@/api/modules/capability'

const loading = ref(false)
const tableData = ref([])
const capabilities = ref([])
const stats = ref({ total: 0, succeeded: 0, failed: 0, running: 0 })
const detailVisible = ref(false)
const currentJob = ref(null)

const filterForm = reactive({
  status: '',
  capability: ''
})

const pagination = reactive({
  page: 1,
  pageSize: 10,
  total: 0
})

const fetchStats = async () => {
  try {
    const response = await getTaskJobStats()
    stats.value = response?.data ?? response
  } catch (error) {
    // ignore
  }
}

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
    const response = await getTaskJobs(params)
    const data = response?.data ?? response
    tableData.value = Array.isArray(data) ? data : (data?.results || [])
    pagination.total = data?.count || (Array.isArray(data) ? data.length : 0)
  } catch (error) {
    console.error('获取任务列表失败:', error)
  } finally {
    loading.value = false
  }
}

const loadCapabilities = async () => {
  try {
    const response = await getCapabilities({ page_size: 200 })
    const data = response?.data ?? response
    capabilities.value = Array.isArray(data) ? data : (data?.results || [])
  } catch (error) {
    capabilities.value = []
  }
}

const resetFilter = () => {
  filterForm.status = ''
  filterForm.capability = ''
  pagination.page = 1
  fetchData()
}

const openDetail = (row) => {
  currentJob.value = row
  detailVisible.value = true
}

const retryJob = async (row) => {
  try {
    await ElMessageBox.confirm(`确定要重新执行任务「${row.job_id}」吗？`, '重试确认', {
      confirmButtonText: '重新执行',
      cancelButtonText: '取消',
      type: 'warning'
    })
    const response = await executeTaskJob(row.id, row.input_data)
    ElMessage.success('已重新执行')
    fetchData()
  } catch (error) {
    if (error !== 'cancel') console.error('重试失败:', error)
  }
}

const getStatusType = (status) => {
  const types = {
    queued: 'info',
    running: 'warning',
    succeeded: 'success',
    failed: 'danger'
  }
  return types[status] || 'info'
}

const duration = (start, end) => {
  const ms = new Date(end) - new Date(start)
  if (isNaN(ms)) return '-'
  if (ms < 1000) return `${ms}ms`
  return `${(ms / 1000).toFixed(1)}s`
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
  fetchData()
  fetchStats()
  loadCapabilities()
})
</script>

<style scoped lang="scss">
.task-job-list {
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
    margin: 0;
    font-size: 13px;
    color: #909399;
  }
}

.stats-row {
  margin-bottom: 16px;

  .stat-card {
    .stat-value {
      font-size: 26px;
      font-weight: 700;
      color: #303133;
    }

    .stat-label {
      font-size: 13px;
      color: #909399;
      margin-top: 4px;
    }

    &.success .stat-value {
      color: #67c23a;
    }

    &.warning .stat-value {
      color: #e6a23c;
    }

    &.danger .stat-value {
      color: #f56c6c;
    }
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

.job-detail {
  .detail-section {
    margin-top: 20px;

    .section-title {
      font-size: 14px;
      font-weight: 600;
      color: #303133;
      margin-bottom: 8px;

      &.error {
        color: #f56c6c;
      }
    }

    .json-block {
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
</style>
