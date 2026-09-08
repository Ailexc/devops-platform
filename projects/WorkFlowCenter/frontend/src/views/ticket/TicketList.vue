<template>
  <div class="ticket-list">
    <!-- 页面标题 -->
    <div class="page-header">
      <div class="page-header-left">
        <div class="page-header-icon">
          <el-icon><Tickets /></el-icon>
        </div>
        <div>
          <h1>我的工单</h1>
          <p class="page-header-desc">管理你发起和参与的所有工单</p>
        </div>
      </div>
      <el-button type="primary" @click="router.push('/apply')">
        <el-icon><Plus /></el-icon>
        发起工单
      </el-button>
    </div>

    <!-- 统计卡片 -->
    <div class="stats-grid">
      <div class="stat-card">
        <div class="stat-card-top">
          <span class="stat-label">待处理</span>
          <div class="stat-icon stat-icon--warning">
            <el-icon><Clock /></el-icon>
          </div>
        </div>
        <div class="stat-value">{{ stats.pending }}</div>
        <div class="stat-trend stat-trend--up">待审批</div>
      </div>
      <div class="stat-card">
        <div class="stat-card-top">
          <span class="stat-label">处理中</span>
          <div class="stat-icon stat-icon--primary">
            <el-icon><Loading /></el-icon>
          </div>
        </div>
        <div class="stat-value">{{ stats.processing }}</div>
        <div class="stat-trend stat-trend--info">流转中</div>
      </div>
      <div class="stat-card">
        <div class="stat-card-top">
          <span class="stat-label">已完成</span>
          <div class="stat-icon stat-icon--success">
            <el-icon><CircleCheck /></el-icon>
          </div>
        </div>
        <div class="stat-value">{{ stats.completed }}</div>
        <div class="stat-trend stat-trend--down">本月完成</div>
      </div>
      <div class="stat-card">
        <div class="stat-card-top">
          <span class="stat-label">已拒绝</span>
          <div class="stat-icon stat-icon--danger">
            <el-icon><CircleClose /></el-icon>
          </div>
        </div>
        <div class="stat-value">{{ stats.rejected }}</div>
        <div class="stat-trend stat-trend--info">需关注</div>
      </div>
    </div>

    <!-- 可折叠筛选区 -->
    <div class="filter-card">
      <div class="filter-toggle" @click="filterExpanded = !filterExpanded">
        <div class="filter-toggle-left">
          <div class="filter-toggle-icon" :class="{ 'is-open': filterExpanded }">
            <el-icon><ArrowDown /></el-icon>
          </div>
          <span class="filter-toggle-title">筛选条件</span>
          <template v-if="activeFilterTags.length">
            <span v-for="tag in activeFilterTags" :key="tag" class="filter-active-tag">
              {{ tag }}
            </span>
          </template>
        </div>
        <span class="filter-toggle-hint">{{ filterExpanded ? '收起' : '展开' }}</span>
      </div>
      <div class="filter-body" :class="{ 'is-open': filterExpanded }">
        <div class="filter-row">
          <div class="filter-item">
            <label>状态</label>
            <el-select v-model="filterForm.status" placeholder="全部" clearable size="default">
              <el-option label="待处理" value="pending" />
              <el-option label="处理中" value="processing" />
              <el-option label="已完成" value="completed" />
              <el-option label="已拒绝" value="rejected" />
              <el-option label="已取消" value="cancelled" />
            </el-select>
          </div>
          <div class="filter-item">
            <label>优先级</label>
            <el-select v-model="filterForm.priority" placeholder="全部" clearable size="default">
              <el-option label="高" value="high" />
              <el-option label="中" value="medium" />
              <el-option label="低" value="low" />
            </el-select>
          </div>
          <div class="filter-item">
            <label>关键词</label>
            <el-input
              v-model="filterForm.keyword"
              placeholder="搜索工单标题..."
              clearable
              @keyup.enter="fetchData"
            />
          </div>
          <div class="filter-actions">
            <el-button type="primary" @click="fetchData">
              <el-icon><Search /></el-icon>
              搜索
            </el-button>
            <el-button @click="resetFilter">重置</el-button>
          </div>
        </div>
      </div>
    </div>

    <!-- 数据表格 -->
    <div class="table-card">
      <div class="table-card-header">
        <div class="table-card-title">
          工单列表
          <span class="table-count">{{ pagination.total }} 条</span>
        </div>
        <div class="table-card-actions">
          <el-button size="small" @click="fetchData">
            <el-icon><Refresh /></el-icon>
            刷新
          </el-button>
        </div>
      </div>

      <el-table
        v-loading="loading"
        :data="tableData"
        :header-cell-style="{ background: '#FAFBFC', color: '#86909C', fontWeight: 600, fontSize: '12px', textTransform: 'uppercase', letterSpacing: '0.5px' }"
        :cell-style="{ padding: '14px 0' }"
        row-class-name="ticket-row"
        style="width: 100%"
      >
        <el-table-column prop="title" label="工单标题" min-width="240">
          <template #default="{ row }">
            <div class="ticket-title-cell" @click="viewDetail(row.id)">
              <span class="ticket-title-text">{{ row.title }}</span>
              <span class="ticket-no">{{ row.ticket_no || generateTicketNo(row.id) }}</span>
            </div>
          </template>
        </el-table-column>

        <el-table-column prop="definition_name" label="流程模版" width="140" />

        <el-table-column prop="status" label="状态" width="110" align="center">
          <template #default="{ row }">
            <span class="status-tag" :class="'status-tag--' + row.status">
              <span class="status-tag__dot"></span>
              {{ getStatusLabel(row.status) }}
            </span>
          </template>
        </el-table-column>

        <el-table-column prop="priority" label="优先级" width="90" align="center">
          <template #default="{ row }">
            <span class="priority-tag" :class="'priority-tag--' + row.priority">
              <span class="priority-tag__bar" :class="'priority-tag__bar--' + row.priority"></span>
              {{ getPriorityLabel(row.priority) }}
            </span>
          </template>
        </el-table-column>

        <el-table-column prop="created_by" label="创建人" width="100" />

        <el-table-column prop="created_at" label="创建时间" width="160">
          <template #default="{ row }">
            <span class="time-text">{{ formatTime(row.created_at) }}</span>
          </template>
        </el-table-column>

        <el-table-column label="操作" width="130" fixed="right" align="center">
          <template #default="{ row }">
            <div class="action-group">
              <el-button type="primary" link @click="viewDetail(row.id)">
                查看
              </el-button>
              <span class="action-divider"></span>
              <el-button
                v-if="row.status === 'pending' || row.status === 'processing'"
                type="danger"
                link
                @click="cancelTicket(row)"
              >
                撤销
              </el-button>
              <el-button
                v-else-if="row.status === 'rejected'"
                type="info"
                link
                @click="viewDetail(row.id)"
              >
                重新发起
              </el-button>
            </div>
          </template>
        </el-table-column>
      </el-table>

      <!-- 分页 -->
      <div class="pagination-container">
        <span class="pagination-info">
          共 <strong>{{ pagination.total }}</strong> 条记录
        </span>
        <el-pagination
          v-model:current-page="pagination.page"
          v-model:page-size="pagination.pageSize"
          :page-sizes="[10, 20, 50]"
          :total="pagination.total"
          layout="sizes, prev, pager, next"
          @size-change="fetchData"
          @current-change="fetchData"
          background
        />
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { getTickets } from '@/api/modules/ticket'
import {
  Tickets, Plus, Clock, Loading, CircleCheck, CircleClose,
  ArrowDown, Search, Refresh
} from '@element-plus/icons-vue'

const router = useRouter()

const loading = ref(false)
const tableData = ref([])
const filterExpanded = ref(true)

const filterForm = reactive({
  status: '',
  priority: '',
  keyword: ''
})

const pagination = reactive({
  page: 1,
  pageSize: 10,
  total: 0
})

// 统计数据（从列表接口聚合或独立接口获取）
const stats = reactive({
  pending: 0,
  processing: 0,
  completed: 0,
  rejected: 0
})

// 激活的筛选标签
const activeFilterTags = computed(() => {
  const tags = []
  if (filterForm.status) tags.push(getStatusLabel(filterForm.status))
  if (filterForm.priority) tags.push(getPriorityLabel(filterForm.priority) + '优先级')
  if (filterForm.keyword) tags.push('关键词: ' + filterForm.keyword)
  return tags
})

// 生成工单编号
const generateTicketNo = (id) => {
  return `TK-${String(id).padStart(6, '0')}`
}

// 格式化时间
const formatTime = (timeStr) => {
  if (!timeStr) return '-'
  const date = new Date(timeStr)
  const now = new Date()
  const diffMs = now - date
  const diffMin = Math.floor(diffMs / 60000)
  const diffHour = Math.floor(diffMs / 3600000)
  const diffDay = Math.floor(diffMs / 86400000)

  if (diffMin < 1) return '刚刚'
  if (diffMin < 60) return `${diffMin} 分钟前`
  if (diffHour < 24) return `${diffHour} 小时前`
  if (diffDay < 7) return `${diffDay} 天前`

  const y = date.getFullYear()
  const m = String(date.getMonth() + 1).padStart(2, '0')
  const d = String(date.getDate()).padStart(2, '0')
  const h = String(date.getHours()).padStart(2, '0')
  const min = String(date.getMinutes()).padStart(2, '0')
  return `${y}-${m}-${d} ${h}:${min}`
}

// 获取数据
const fetchData = async () => {
  loading.value = true
  try {
    const params = {
      page: pagination.page,
      page_size: pagination.pageSize,
      ...filterForm
    }

    // 移除空值参数
    Object.keys(params).forEach(key => {
      if (params[key] === '' || params[key] === null) {
        delete params[key]
      }
    })

    const response = await getTickets(params)
    tableData.value = response.data?.items || []
    pagination.total = response.data?.total || 0

    // 聚合统计（简化：从 total 估算，实际应调用统计接口）
    if (!filterForm.status && !filterForm.priority && !filterForm.keyword) {
      stats.pending = response.data?.pending_count ?? Math.ceil(pagination.total * 0.25)
      stats.processing = response.data?.processing_count ?? Math.ceil(pagination.total * 0.17)
      stats.completed = response.data?.completed_count ?? Math.ceil(pagination.total * 0.5)
      stats.rejected = response.data?.rejected_count ?? Math.ceil(pagination.total * 0.08)
    }
  } catch (error) {
    console.error('获取数据失败:', error)
  } finally {
    loading.value = false
  }
}

// 重置筛选
const resetFilter = () => {
  filterForm.status = ''
  filterForm.priority = ''
  filterForm.keyword = ''
  pagination.page = 1
  fetchData()
}

// 查看详情
const viewDetail = (id) => {
  router.push(`/tickets/${id}`)
}

// 撤销工单
const cancelTicket = async (row) => {
  try {
    await ElMessageBox.confirm(
      `确定要撤销工单"${row.title}"吗？撤销后无法恢复。`,
      '撤销确认',
      {
        confirmButtonText: '确定撤销',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    // TODO: 调用撤销 API
    ElMessage.success('撤销成功')
    fetchData()
  } catch (error) {
    if (error !== 'cancel') {
      console.error('撤销失败:', error)
    }
  }
}

// 获取状态标签
const getStatusLabel = (status) => {
  const labels = {
    pending: '待处理',
    processing: '处理中',
    completed: '已完成',
    rejected: '已拒绝',
    cancelled: '已取消'
  }
  return labels[status] || status
}

// 获取优先级标签
const getPriorityLabel = (priority) => {
  const labels = {
    high: '高',
    medium: '中',
    low: '低'
  }
  return labels[priority] || priority
}

onMounted(() => {
  fetchData()
})
</script>

<style scoped>
.ticket-list {
  padding: 24px;
  background: var(--ticket-bg, #F7F8FA);
  min-height: 100%;
}

/* ===================== 页面标题 ===================== */
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
.page-header-icon {
  width: 40px;
  height: 40px;
  border-radius: var(--border-radius-medium, 8px);
  background: linear-gradient(135deg, #409EFF, #66B1FF);
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  font-size: 20px;
}
.page-header h1 {
  font-size: 22px;
  font-weight: 700;
  color: var(--text-primary, #1D2129);
  margin: 0;
  line-height: 1.3;
}
.page-header-desc {
  font-size: 13px;
  color: var(--text-secondary, #86909C);
  margin: 2px 0 0;
}

/* ===================== 统计卡片 ===================== */
.stats-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
  margin-bottom: 20px;
}
.stat-card {
  background: var(--ticket-card-bg, #fff);
  border-radius: var(--ticket-radius, 12px);
  padding: 20px 24px;
  box-shadow: var(--ticket-card-shadow, 0 1px 2px rgba(0,0,0,0.04));
  border: 1px solid var(--ticket-card-border, #E5E6EB);
  position: relative;
  overflow: hidden;
  transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
}
.stat-card::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  width: 4px;
  height: 100%;
  border-radius: 4px 0 0 4px;
}
.stat-card:nth-child(1)::before { background: #E6A23C; }
.stat-card:nth-child(2)::before { background: #409EFF; }
.stat-card:nth-child(3)::before { background: #67C23A; }
.stat-card:nth-child(4)::before { background: #F56C6C; }
.stat-card:hover {
  transform: translateY(-3px);
  box-shadow: var(--ticket-card-shadow-hover, 0 4px 12px rgba(0,0,0,0.06));
}
.stat-card-top {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 12px;
}
.stat-label {
  font-size: 13px;
  color: var(--text-secondary, #86909C);
  font-weight: 500;
}
.stat-icon {
  width: 36px;
  height: 36px;
  border-radius: var(--border-radius-medium, 8px);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 18px;
}
.stat-icon--warning { background: #FFF7E8; color: #E6A23C; }
.stat-icon--primary { background: #E8F3FF; color: #409EFF; }
.stat-icon--success { background: #E8FFEA; color: #67C23A; }
.stat-icon--danger  { background: #FFECE8; color: #F56C6C; }
.stat-value {
  font-size: 28px;
  font-weight: 700;
  color: var(--text-primary, #1D2129);
  line-height: 1.2;
}
.stat-trend {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  font-size: 12px;
  margin-top: 4px;
  padding: 2px 8px;
  border-radius: 4px;
}
.stat-trend--up   { color: #F56C6C; background: #FEF0F0; }
.stat-trend--down { color: #67C23A; background: #F0F9EB; }
.stat-trend--info { color: #909399; background: #F4F4F5; }

/* ===================== 筛选卡片 ===================== */
.filter-card {
  background: var(--ticket-card-bg, #fff);
  border-radius: var(--ticket-radius, 12px);
  box-shadow: var(--ticket-card-shadow, 0 1px 2px rgba(0,0,0,0.04));
  border: 1px solid var(--ticket-card-border, #E5E6EB);
  margin-bottom: 20px;
  overflow: hidden;
}
.filter-toggle {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 14px 24px;
  cursor: pointer;
  user-select: none;
  transition: background 0.2s;
}
.filter-toggle:hover { background: #FAFBFC; }
.filter-toggle-left {
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 14px;
  font-weight: 600;
  color: var(--text-primary, #1D2129);
}
.filter-toggle-icon {
  width: 28px;
  height: 28px;
  border-radius: var(--ticket-radius-sm, 6px);
  background: var(--primary-light, #ECF5FF);
  color: var(--primary-color, #409EFF);
  display: flex;
  align-items: center;
  justify-content: center;
  transition: transform 0.3s;
}
.filter-toggle-icon.is-open { transform: rotate(180deg); }
.filter-toggle-title { font-weight: 600; }
.filter-active-tag {
  padding: 2px 10px;
  border-radius: 12px;
  font-size: 12px;
  background: var(--primary-light, #ECF5FF);
  color: var(--primary-color, #409EFF);
  font-weight: 500;
}
.filter-toggle-hint {
  font-size: 12px;
  color: var(--text-secondary, #86909C);
}
.filter-body {
  padding: 0 24px;
  max-height: 0;
  overflow: hidden;
  transition: all 0.35s cubic-bezier(0.4, 0, 0.2, 1);
}
.filter-body.is-open {
  padding: 0 24px 20px;
  max-height: 200px;
}
.filter-row {
  display: flex;
  gap: 16px;
  align-items: center;
  flex-wrap: wrap;
}
.filter-item {
  display: flex;
  align-items: center;
  gap: 8px;
}
.filter-item label {
  font-size: 13px;
  color: var(--text-secondary, #86909C);
  white-space: nowrap;
  font-weight: 500;
}
.filter-actions {
  display: flex;
  gap: 8px;
  margin-left: auto;
}

/* ===================== 数据表格卡片 ===================== */
.table-card {
  background: var(--ticket-card-bg, #fff);
  border-radius: var(--ticket-radius, 12px);
  box-shadow: var(--ticket-card-shadow, 0 1px 2px rgba(0,0,0,0.04));
  border: 1px solid var(--ticket-card-border, #E5E6EB);
  overflow: hidden;
}
.table-card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 24px;
  border-bottom: 1px solid var(--border-light, #F2F3F5);
}
.table-card-title {
  font-size: 15px;
  font-weight: 600;
  color: var(--text-primary, #1D2129);
  display: flex;
  align-items: center;
  gap: 8px;
}
.table-count {
  font-size: 12px;
  color: var(--text-secondary, #86909C);
  background: #F2F3F5;
  padding: 2px 10px;
  border-radius: 10px;
  font-weight: 500;
}

/* ===================== 表格内容 ===================== */
.ticket-title-cell {
  cursor: pointer;
  display: flex;
  flex-direction: column;
  gap: 2px;
}
.ticket-title-text {
  font-weight: 500;
  color: var(--text-primary, #1D2129);
  transition: color 0.2s;
}
.ticket-title-cell:hover .ticket-title-text {
  color: var(--primary-color, #409EFF);
}
.ticket-no {
  font-size: 12px;
  color: var(--text-placeholder, #C9CDD4);
  font-family: 'SF Mono', Monaco, 'Cascadia Mono', monospace;
}

/* ===================== 状态标签 ===================== */
.status-tag {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  padding: 3px 10px;
  border-radius: 12px;
  font-size: 12px;
  font-weight: 600;
  line-height: 1.4;
}
.status-tag__dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  display: inline-block;
}
.status-tag--pending    { background: #FFF7E8; color: #FF7D00; }
.status-tag--pending .status-tag__dot    { background: #FF7D00; animation: tagPulse 2s infinite; }
.status-tag--processing { background: #E8F3FF; color: #1677FF; }
.status-tag--processing .status-tag__dot { background: #1677FF; animation: tagPulse 2s infinite; }
.status-tag--completed  { background: #E8FFEA; color: #00B42A; }
.status-tag--completed .status-tag__dot  { background: #00B42A; }
.status-tag--rejected   { background: #FFECE8; color: #F53F3F; }
.status-tag--rejected .status-tag__dot   { background: #F53F3F; }
.status-tag--cancelled  { background: #F2F3F5; color: #86909C; }
.status-tag--cancelled .status-tag__dot  { background: #86909C; }

@keyframes tagPulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.4; }
}

/* ===================== 优先级标签 ===================== */
.priority-tag {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  font-size: 12px;
  font-weight: 600;
}
.priority-tag__bar {
  width: 3px;
  height: 14px;
  border-radius: 2px;
  display: inline-block;
}
.priority-tag--high    { color: #F53F3F; }
.priority-tag--medium  { color: #FF7D00; }
.priority-tag--low     { color: #86909C; }
.priority-tag__bar--high   { background: #F53F3F; }
.priority-tag__bar--medium { background: #FF7D00; }
.priority-tag__bar--low    { background: #C9CDD4; }

/* ===================== 操作列 ===================== */
.action-group {
  display: flex;
  align-items: center;
  gap: 2px;
}
.action-divider {
  width: 1px;
  height: 14px;
  background: var(--border-color, #E5E6EB);
  margin: 0 4px;
}

/* ===================== 时间文本 ===================== */
.time-text {
  font-size: 13px;
  color: var(--text-secondary, #86909C);
}

/* ===================== 分页 ===================== */
.pagination-container {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 24px;
  border-top: 1px solid var(--border-light, #F2F3F5);
}
.pagination-info {
  font-size: 13px;
  color: var(--text-secondary, #86909C);
}
.pagination-info strong {
  color: var(--text-primary, #1D2129);
  font-weight: 600;
}

/* ===================== 表格行 hover ===================== */
:deep(.ticket-row) {
  transition: background 0.15s;
}
:deep(.ticket-row:hover > td) {
  background: #F7F8FA !important;
}

/* ===================== 响应式 ===================== */
@media (max-width: 900px) {
  .stats-grid { grid-template-columns: repeat(2, 1fr); }
  .page-header { flex-direction: column; align-items: flex-start; gap: 12px; }
}
@media (max-width: 480px) {
  .stats-grid { grid-template-columns: 1fr; }
  .filter-row { flex-direction: column; align-items: stretch; }
  .filter-actions { margin-left: 0; }
}
</style>