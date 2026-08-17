<template>
  <div class="my-applications">
    <!-- 页面标题 -->
    <div class="page-header">
      <div class="page-header-left">
        <div class="page-header-icon">
          <el-icon><Tickets /></el-icon>
        </div>
        <div>
          <h1>我的申请</h1>
          <p class="page-header-desc">管理你发起的所有流程申请</p>
        </div>
      </div>
      <el-button type="primary" @click="$router.push('/apply')">
        <el-icon><Plus /></el-icon>
        发起申请
      </el-button>
    </div>

    <!-- 统计卡片 -->
    <div class="stats-grid">
      <div class="stat-card">
        <div class="stat-card-top">
          <span class="stat-label">运行中</span>
          <div class="stat-icon stat-icon--primary"><el-icon><Loading /></el-icon></div>
        </div>
        <div class="stat-value">{{ stats.running }}</div>
      </div>
      <div class="stat-card">
        <div class="stat-card-top">
          <span class="stat-label">已挂起</span>
          <div class="stat-icon stat-icon--warning"><el-icon><Clock /></el-icon></div>
        </div>
        <div class="stat-value">{{ stats.suspended }}</div>
      </div>
      <div class="stat-card">
        <div class="stat-card-top">
          <span class="stat-label">已完成</span>
          <div class="stat-icon stat-icon--success"><el-icon><CircleCheck /></el-icon></div>
        </div>
        <div class="stat-value">{{ stats.completed }}</div>
      </div>
      <div class="stat-card">
        <div class="stat-card-top">
          <span class="stat-label">已终止</span>
          <div class="stat-icon stat-icon--danger"><el-icon><CircleClose /></el-icon></div>
        </div>
        <div class="stat-value">{{ stats.terminated }}</div>
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
            <span v-for="tag in activeFilterTags" :key="tag" class="filter-active-tag">{{ tag }}</span>
          </template>
        </div>
        <span class="filter-toggle-hint">{{ filterExpanded ? '收起' : '展开' }}</span>
      </div>
      <div class="filter-body" :class="{ 'is-open': filterExpanded }">
        <div class="filter-row">
          <div class="filter-item">
            <label>状态</label>
            <el-select v-model="filterForm.status" placeholder="全部" clearable>
              <el-option v-for="s in statusOptions" :key="s.value" :label="s.label" :value="s.value" />
            </el-select>
          </div>
          <div class="filter-item">
            <label>关键词</label>
            <el-input
              v-model="filterForm.keyword"
              placeholder="搜索单号 / 标题..."
              clearable
              @keyup.enter="fetchData"
            />
          </div>
          <div class="filter-actions">
            <el-button type="primary" @click="fetchData">
              <el-icon><Search /></el-icon> 搜索
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
          申请列表
          <span class="table-count">{{ pagination.total }} 条</span>
        </div>
        <el-button size="small" @click="fetchData">
          <el-icon><Refresh /></el-icon> 刷新
        </el-button>
      </div>

      <el-table
        v-loading="loading"
        :data="tableData"
        :header-cell-style="{ background: '#FAFBFC', color: '#86909C', fontWeight: 600, fontSize: '12px', textTransform: 'uppercase', letterSpacing: '0.5px' }"
        :cell-style="{ padding: '14px 0' }"
        row-class-name="ticket-row"
        style="width: 100%"
      >
        <el-table-column prop="instance_no" label="单号" width="160">
          <template #default="{ row }">
            <div class="ticket-title-cell" @click="viewDetail(row)">
              <span class="ticket-title-text">{{ row.instance_no }}</span>
            </div>
          </template>
        </el-table-column>
        <el-table-column prop="definition_name" label="流程" width="140" />
        <el-table-column label="标题" min-width="180">
          <template #default="{ row }">
            <span class="ticket-title-text">{{ row.business_key || row.definition_name }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="status_display" label="状态" width="110" align="center">
          <template #default="{ row }">
            <span class="status-tag" :class="'status-tag--' + row.status">
              <span class="status-tag__dot"></span>
              {{ row.status_display }}
            </span>
          </template>
        </el-table-column>
        <el-table-column prop="current_node_key" label="当前节点" width="120" />
        <el-table-column prop="started_at" label="发起时间" width="160">
          <template #default="{ row }">
            <span class="time-text">{{ formatTime(row.started_at) }}</span>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="100" fixed="right" align="center">
          <template #default="{ row }">
            <el-button type="primary" link @click="viewDetail(row)">详情</el-button>
          </template>
        </el-table-column>
      </el-table>

      <div class="pagination-container">
        <span class="pagination-info">共 <strong>{{ pagination.total }}</strong> 条记录</span>
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
import { Plus, Tickets, Loading, Clock, CircleCheck, CircleClose, ArrowDown, Search, Refresh } from '@element-plus/icons-vue'
import { getInstances } from '@/api/modules/process'

const router = useRouter()

const loading = ref(false)
const tableData = ref([])
const filterExpanded = ref(true)

const filterForm = reactive({ status: '', keyword: '' })
const pagination = reactive({ page: 1, pageSize: 10, total: 0 })
const stats = reactive({ running: 0, suspended: 0, completed: 0, terminated: 0 })

const statusOptions = [
  { value: 'running', label: '运行中' },
  { value: 'suspended', label: '已挂起' },
  { value: 'completed', label: '已完成' },
  { value: 'terminated', label: '已终止' }
]

const activeFilterTags = computed(() => {
  const tags = []
  if (filterForm.status) {
    const opt = statusOptions.find(s => s.value === filterForm.status)
    if (opt) tags.push(opt.label)
  }
  if (filterForm.keyword) tags.push('关键词: ' + filterForm.keyword)
  return tags
})

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
  const m = String(date.getMonth() + 1).padStart(2, '0')
  const d = String(date.getDate()).padStart(2, '0')
  const h = String(date.getHours()).padStart(2, '0')
  const min = String(date.getMinutes()).padStart(2, '0')
  return `${m}-${d} ${h}:${min}`
}

const fetchData = async () => {
  loading.value = true
  try {
    const params = { mine: 1, page: pagination.page, page_size: pagination.pageSize, ...filterForm }
    Object.keys(params).forEach(key => {
      if (params[key] === '' || params[key] === null) delete params[key]
    })
    const response = await getInstances(params)
    const data = response?.data ?? response
    tableData.value = Array.isArray(data) ? data : (data?.results || [])
    pagination.total = data?.count || (Array.isArray(data) ? data.length : 0)

    if (!filterForm.status && !filterForm.keyword) {
      stats.running = tableData.value.filter(r => r.status === 'running').length
      stats.suspended = tableData.value.filter(r => r.status === 'suspended').length
      stats.completed = tableData.value.filter(r => r.status === 'completed').length
      stats.terminated = tableData.value.filter(r => r.status === 'terminated').length
    }
  } catch (error) {
    console.error('获取申请列表失败:', error)
  } finally {
    loading.value = false
  }
}

const resetFilter = () => {
  filterForm.status = ''
  filterForm.keyword = ''
  pagination.page = 1
  fetchData()
}

const viewDetail = (row) => {
  router.push(`/my/applications/${row.id}`)
}

onMounted(() => {
  fetchData()
})
</script>

<style scoped lang="scss">
.my-applications {
  padding: 24px;
  background: var(--ticket-bg, #F7F8FA);
  min-height: 100%;
}

/* 页面标题 */
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
  width: 40px; height: 40px;
  border-radius: var(--border-radius-medium, 8px);
  background: linear-gradient(135deg, #409EFF, #66B1FF);
  display: flex; align-items: center; justify-content: center;
  color: #fff; font-size: 20px;
}
.page-header h1 {
  font-size: 22px; font-weight: 700; color: var(--text-primary, #1D2129);
  margin: 0; line-height: 1.3;
}
.page-header-desc {
  font-size: 13px; color: var(--text-secondary, #86909C); margin: 2px 0 0;
}

/* 统计卡片 */
.stats-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
  margin-bottom: 20px;
}
.stat-card {
  background: #fff;
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
  top: 0; left: 0;
  width: 4px; height: 100%;
  border-radius: 4px 0 0 4px;
}
.stat-card:nth-child(1)::before { background: #409EFF; }
.stat-card:nth-child(2)::before { background: #E6A23C; }
.stat-card:nth-child(3)::before { background: #67C23A; }
.stat-card:nth-child(4)::before { background: #F56C6C; }
.stat-card:hover {
  transform: translateY(-3px);
  box-shadow: var(--ticket-card-shadow-hover, 0 4px 12px rgba(0,0,0,0.06));
}
.stat-card-top {
  display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 12px;
}
.stat-label {
  font-size: 13px; color: var(--text-secondary, #86909C); font-weight: 500;
}
.stat-icon {
  width: 36px; height: 36px;
  border-radius: var(--border-radius-medium, 8px);
  display: flex; align-items: center; justify-content: center; font-size: 18px;
}
.stat-icon--primary { background: #E8F3FF; color: #409EFF; }
.stat-icon--warning { background: #FFF7E8; color: #E6A23C; }
.stat-icon--success { background: #E8FFEA; color: #67C23A; }
.stat-icon--danger  { background: #FFECE8; color: #F56C6C; }
.stat-value {
  font-size: 28px; font-weight: 700; color: var(--text-primary, #1D2129); line-height: 1.2;
}

/* 筛选卡片 */
.filter-card {
  background: #fff;
  border-radius: var(--ticket-radius, 12px);
  box-shadow: var(--ticket-card-shadow, 0 1px 2px rgba(0,0,0,0.04));
  border: 1px solid var(--ticket-card-border, #E5E6EB);
  margin-bottom: 20px;
  overflow: hidden;
}
.filter-toggle {
  display: flex; align-items: center; justify-content: space-between;
  padding: 14px 24px; cursor: pointer; user-select: none;
  transition: background 0.2s;
  &:hover { background: #FAFBFC; }
}
.filter-toggle-left {
  display: flex; align-items: center; gap: 10px;
  font-size: 14px; font-weight: 600; color: var(--text-primary, #1D2129);
}
.filter-toggle-icon {
  width: 28px; height: 28px;
  border-radius: var(--ticket-radius-sm, 6px);
  background: var(--primary-light, #ECF5FF);
  color: var(--primary-color, #409EFF);
  display: flex; align-items: center; justify-content: center;
  transition: transform 0.3s;
  &.is-open { transform: rotate(180deg); }
}
.filter-active-tag {
  padding: 2px 10px; border-radius: 12px; font-size: 12px;
  background: var(--primary-light, #ECF5FF);
  color: var(--primary-color, #409EFF); font-weight: 500;
}
.filter-toggle-hint {
  font-size: 12px; color: var(--text-secondary, #86909C);
}
.filter-body {
  padding: 0 24px; max-height: 0; overflow: hidden;
  transition: all 0.35s cubic-bezier(0.4, 0, 0.2, 1);
  &.is-open { padding: 0 24px 20px; max-height: 200px; }
}
.filter-row {
  display: flex; gap: 16px; align-items: center; flex-wrap: wrap;
}
.filter-item {
  display: flex; align-items: center; gap: 8px;
  label {
    font-size: 13px; color: var(--text-secondary, #86909C); white-space: nowrap; font-weight: 500;
  }
}
.filter-actions {
  display: flex; gap: 8px; margin-left: auto;
}

/* 表格卡片 */
.table-card {
  background: #fff;
  border-radius: var(--ticket-radius, 12px);
  box-shadow: var(--ticket-card-shadow, 0 1px 2px rgba(0,0,0,0.04));
  border: 1px solid var(--ticket-card-border, #E5E6EB);
  overflow: hidden;
}
.table-card-header {
  display: flex; justify-content: space-between; align-items: center;
  padding: 16px 24px; border-bottom: 1px solid #F2F3F5;
}
.table-card-title {
  font-size: 15px; font-weight: 600; color: var(--text-primary, #1D2129);
  display: flex; align-items: center; gap: 8px;
}
.table-count {
  font-size: 12px; color: var(--text-secondary, #86909C);
  background: #F2F3F5; padding: 2px 10px; border-radius: 10px; font-weight: 500;
}

/* 表格内容 */
.ticket-title-cell {
  cursor: pointer;
  &:hover .ticket-title-text { color: var(--primary-color, #409EFF); }
}
.ticket-title-text {
  font-weight: 500; color: var(--text-primary, #1D2129); transition: color 0.2s;
}
.time-text { font-size: 13px; color: var(--text-secondary, #86909C); }

/* 状态标签 */
.status-tag {
  display: inline-flex; align-items: center; gap: 5px;
  padding: 3px 10px; border-radius: 12px; font-size: 12px; font-weight: 600;
}
.status-tag__dot {
  width: 6px; height: 6px; border-radius: 50%;
}
.status-tag--running    { background: #E8F3FF; color: #1677FF; }
.status-tag--running .status-tag__dot    { background: #1677FF; animation: tagPulse 2s infinite; }
.status-tag--suspended  { background: #FFF7E8; color: #FF7D00; }
.status-tag--suspended .status-tag__dot  { background: #FF7D00; animation: tagPulse 2s infinite; }
.status-tag--completed  { background: #E8FFEA; color: #00B42A; }
.status-tag--completed .status-tag__dot  { background: #00B42A; }
.status-tag--terminated { background: #F2F3F5; color: #86909C; }
.status-tag--terminated .status-tag__dot { background: #86909C; }
@keyframes tagPulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.4; }
}

/* 分页 */
.pagination-container {
  display: flex; justify-content: space-between; align-items: center;
  padding: 16px 24px; border-top: 1px solid #F2F3F5;
}
.pagination-info {
  font-size: 13px; color: var(--text-secondary, #86909C);
  strong { color: var(--text-primary, #1D2129); font-weight: 600; }
}

/* 表格行 hover */
:deep(.ticket-row) { transition: background 0.15s; }
:deep(.ticket-row:hover > td) { background: #F7F8FA !important; }

/* 响应式 */
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
