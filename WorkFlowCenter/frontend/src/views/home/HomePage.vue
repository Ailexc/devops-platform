<template>
  <div class="home-page">
    <!-- 欢迎区 -->
    <div class="welcome-section">
      <div class="welcome-left">
        <h1>工作台</h1>
        <p class="welcome-desc">欢迎回来，{{ authStore.user?.username || '用户' }}！这是你的工作台概览。</p>
      </div>
      <el-button type="primary" size="large" @click="$router.push('/apply')">
        <el-icon><Plus /></el-icon>
        发起申请
      </el-button>
    </div>

    <!-- 统计卡片 -->
    <div class="stats-grid">
      <div class="stat-card stat-card--primary" @click="$router.push('/my/todo')">
        <div class="stat-card-top">
          <span class="stat-label">待办任务</span>
          <div class="stat-icon"><el-icon :size="20"><Clock /></el-icon></div>
        </div>
        <div class="stat-value">{{ stats.todoCount }}</div>
        <div class="stat-footer">需要你处理的审批</div>
      </div>
      <div class="stat-card stat-card--success" @click="$router.push('/my/done')">
        <div class="stat-card-top">
          <span class="stat-label">已办任务</span>
          <div class="stat-icon"><el-icon :size="20"><CircleCheck /></el-icon></div>
        </div>
        <div class="stat-value">{{ stats.doneCount }}</div>
        <div class="stat-footer">已完成的审批</div>
      </div>
      <div class="stat-card stat-card--warning" @click="$router.push('/my/applications')">
        <div class="stat-card-top">
          <span class="stat-label">我发起的</span>
          <div class="stat-icon"><el-icon :size="20"><Promotion /></el-icon></div>
        </div>
        <div class="stat-value">{{ stats.createdCount }}</div>
        <div class="stat-footer">我的流程申请</div>
      </div>
      <div class="stat-card stat-card--danger" @click="$router.push('/my/cc')">
        <div class="stat-card-top">
          <span class="stat-label">抄送我的</span>
          <div class="stat-icon"><el-icon :size="20"><ChatDotRound /></el-icon></div>
        </div>
        <div class="stat-value">{{ stats.ccCount }}</div>
        <div class="stat-footer">与你相关的通知</div>
      </div>
    </div>

    <!-- 快捷入口 -->
    <div class="section-card">
      <div class="section-header">
        <div class="section-title">
          <span class="section-title__bar"></span>
          快捷入口
        </div>
      </div>
      <div class="quick-grid">
        <div class="quick-item" @click="$router.push('/apply')">
          <div class="quick-icon quick-icon--blue"><el-icon :size="24"><Plus /></el-icon></div>
          <span class="quick-label">发起申请</span>
        </div>
        <div class="quick-item" @click="$router.push('/my/todo')">
          <div class="quick-icon quick-icon--orange"><el-icon :size="24"><Finished /></el-icon></div>
          <span class="quick-label">待办审批</span>
        </div>
        <div class="quick-item" @click="$router.push('/my/applications')">
          <div class="quick-icon quick-icon--green"><el-icon :size="24"><Tickets /></el-icon></div>
          <span class="quick-label">我的申请</span>
        </div>
        <div class="quick-item" @click="$router.push('/admin/process-definitions')">
          <div class="quick-icon quick-icon--purple"><el-icon :size="24"><Document /></el-icon></div>
          <span class="quick-label">流程配置</span>
        </div>
        <div class="quick-item" @click="$router.push('/my/done')">
          <div class="quick-icon quick-icon--red"><el-icon :size="24"><CircleCheck /></el-icon></div>
          <span class="quick-label">已办审批</span>
        </div>
      </div>
    </div>

    <!-- 最近工单 -->
    <div class="section-card">
      <div class="section-header">
        <div class="section-title">
          <span class="section-title__bar"></span>
          最近工单
        </div>
        <el-button text type="primary" @click="$router.push('/my/applications')">
          查看更多 <el-icon><ArrowRight /></el-icon>
        </el-button>
      </div>
      <el-table
        v-loading="loading"
        :data="recentTickets"
        :header-cell-style="{ background: '#FAFBFC', color: '#86909C', fontWeight: 600, fontSize: '12px' }"
        :cell-style="{ padding: '12px 0' }"
        style="width: 100%"
      >
        <el-table-column prop="title" label="工单标题" min-width="200">
          <template #default="{ row }">
            <span class="ticket-link" @click="viewTicket(row.id)">
              {{ row.title || row.instance_no || '—' }}
            </span>
          </template>
        </el-table-column>
        <el-table-column prop="definition_name" label="流程" width="140" />
        <el-table-column prop="status" label="状态" width="110" align="center">
          <template #default="{ row }">
            <span class="status-tag" :class="'status-tag--' + row.status">
              <span class="status-tag__dot"></span>
              {{ getStatusLabel(row.status) }}
            </span>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="创建时间" width="160" />
        <el-table-column label="操作" width="80" align="center">
          <template #default="{ row }">
            <el-button type="primary" link @click="viewTicket(row.id)">查看</el-button>
          </template>
        </el-table-column>
      </el-table>
      <div v-if="!loading && recentTickets.length === 0" class="empty-hint">
        暂无工单记录
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { Clock, CircleCheck, Promotion, ChatDotRound, Plus, Finished, Tickets, Document, Bell, ArrowRight } from '@element-plus/icons-vue'
import { getInstances } from '@/api/modules/process'
import { getTickets } from '@/api/modules/ticket'
import { getTasks } from '@/api/modules/task'

const router = useRouter()
const authStore = useAuthStore()

const loading = ref(false)
const recentTickets = ref([])

const stats = reactive({
  todoCount: 0,
  doneCount: 0,
  createdCount: 0,
  ccCount: 0
})

const fetchStats = async () => {
  try {
    const [todoRes, doneRes, createdRes, ccRes] = await Promise.all([
      getTasks({ type: 'todo', page: 1, page_size: 1 }),
      getTasks({ type: 'done', page: 1, page_size: 1 }),
      getInstances({ mine: 1, page: 1, page_size: 1 }),
      getTasks({ type: 'cc', page: 1, page_size: 1 })
    ])
    stats.todoCount = todoRes?.count || 0
    stats.doneCount = doneRes?.count || 0
    stats.createdCount = createdRes?.count || 0
    stats.ccCount = ccRes?.count || 0
  } catch (error) {
    console.error('获取统计数据失败:', error)
  }
}

const fetchRecentTickets = async () => {
  loading.value = true
  try {
    const response = await getTickets({ page: 1, page_size: 5 })
    const data = response?.data ?? response
    recentTickets.value = Array.isArray(data) ? data : (data?.results || [])
  } catch (error) {
    console.error('获取最近工单失败:', error)
  } finally {
    loading.value = false
  }
}

const getStatusLabel = (status) => {
  const labels = {
    pending: '待处理', processing: '处理中', completed: '已完成',
    rejected: '已拒绝', cancelled: '已取消', running: '运行中',
    suspended: '已挂起', terminated: '已终止'
  }
  return labels[status] || status
}

const viewTicket = (id) => {
  router.push(`/my/applications/${id}`)
}

onMounted(() => {
  fetchStats()
  fetchRecentTickets()
})
</script>

<style scoped>
.home-page {
  padding: 24px;
  background: var(--ticket-bg, #F7F8FA);
  min-height: 100%;
}

/* 欢迎区 */
.welcome-section {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
}
.welcome-section h1 {
  font-size: 22px;
  font-weight: 700;
  color: var(--text-primary, #1D2129);
  margin: 0;
}
.welcome-desc {
  font-size: 13px;
  color: var(--text-secondary, #86909C);
  margin: 4px 0 0;
}

/* 统计卡片 */
.stats-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
  margin-bottom: 24px;
}
.stat-card {
  background: #fff;
  border-radius: 12px;
  padding: 20px 24px;
  box-shadow: 0 1px 2px rgba(0,0,0,0.04);
  border: 1px solid #E5E6EB;
  position: relative;
  overflow: hidden;
  cursor: pointer;
  transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
}
.stat-card::before {
  content: '';
  position: absolute;
  top: 0; left: 0;
  width: 4px; height: 100%;
  border-radius: 4px 0 0 4px;
}
.stat-card--primary::before  { background: #409EFF; }
.stat-card--success::before  { background: #67C23A; }
.stat-card--warning::before  { background: #E6A23C; }
.stat-card--danger::before   { background: #F56C6C; }
.stat-card:hover {
  transform: translateY(-3px);
  box-shadow: 0 4px 12px rgba(0,0,0,0.06);
}
.stat-card-top {
  display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 12px;
}
.stat-label {
  font-size: 13px; color: var(--text-secondary, #86909C); font-weight: 500;
}
.stat-icon {
  width: 36px; height: 36px; border-radius: 8px;
  display: flex; align-items: center; justify-content: center;
}
.stat-card--primary .stat-icon { background: #E8F3FF; color: #409EFF; }
.stat-card--success .stat-icon { background: #E8FFEA; color: #67C23A; }
.stat-card--warning .stat-icon { background: #FFF7E8; color: #E6A23C; }
.stat-card--danger .stat-icon  { background: #FFECE8; color: #F56C6C; }
.stat-value {
  font-size: 28px; font-weight: 700; color: var(--text-primary, #1D2129); line-height: 1.2;
}
.stat-footer {
  font-size: 12px; color: var(--text-placeholder, #C9CDD4); margin-top: 4px;
}

/* 通用区块卡片 */
.section-card {
  background: #fff;
  border-radius: 12px;
  box-shadow: 0 1px 2px rgba(0,0,0,0.04);
  border: 1px solid #E5E6EB;
  margin-bottom: 20px;
  overflow: hidden;
}
.section-header {
  display: flex; justify-content: space-between; align-items: center;
  padding: 16px 24px; border-bottom: 1px solid #F2F3F5;
}
.section-title {
  display: flex; align-items: center; gap: 8px;
  font-size: 15px; font-weight: 600; color: var(--text-primary, #1D2129);
}
.section-title__bar {
  width: 3px; height: 16px; background: #409EFF; border-radius: 2px;
}

/* 快捷入口 */
.quick-grid {
  display: grid;
  grid-template-columns: repeat(5, 1fr);
  gap: 0;
}
.quick-item {
  display: flex; flex-direction: column; align-items: center; gap: 10px;
  padding: 28px 16px;
  cursor: pointer;
  transition: background 0.2s;
  border-right: 1px solid #F2F3F5;
}
.quick-item:last-child { border-right: none; }
.quick-item:hover { background: #F7F8FA; }
.quick-icon {
  width: 48px; height: 48px; border-radius: 12px;
  display: flex; align-items: center; justify-content: center;
}
.quick-icon--blue   { background: #E8F3FF; color: #409EFF; }
.quick-icon--orange { background: #FFF7E8; color: #E6A23C; }
.quick-icon--green  { background: #E8FFEA; color: #67C23A; }
.quick-icon--purple { background: #F3E8FF; color: #9B59B6; }
.quick-icon--red    { background: #FFECE8; color: #F56C6C; }
.quick-label {
  font-size: 13px; font-weight: 500; color: var(--text-regular, #4E5969);
}

/* 状态标签 */
.status-tag {
  display: inline-flex; align-items: center; gap: 5px;
  padding: 3px 10px; border-radius: 12px; font-size: 12px; font-weight: 600;
}
.status-tag__dot { width: 6px; height: 6px; border-radius: 50%; }
.status-tag--running    { background: #E8F3FF; color: #1677FF; }
.status-tag--running .status-tag__dot    { background: #1677FF; animation: tagPulse 2s infinite; }
.status-tag--suspended  { background: #FFF7E8; color: #FF7D00; }
.status-tag--completed  { background: #E8FFEA; color: #00B42A; }
.status-tag--completed .status-tag__dot  { background: #00B42A; }
.status-tag--terminated { background: #F2F3F5; color: #86909C; }
.status-tag--pending    { background: #FFF7E8; color: #FF7D00; }
.status-tag--processing { background: #E8F3FF; color: #1677FF; }
.status-tag--rejected   { background: #FFECE8; color: #F53F3F; }
.status-tag--cancelled  { background: #F2F3F5; color: #86909C; }
@keyframes tagPulse { 0%,100%{opacity:1} 50%{opacity:0.4} }

.ticket-link {
  font-weight: 500; color: var(--text-primary, #1D2129);
  cursor: pointer; transition: color 0.2s;
}
.ticket-link:hover { color: #409EFF; }

.empty-hint {
  text-align: center; padding: 40px; font-size: 14px; color: var(--text-secondary, #86909C);
}

/* 响应式 */
@media (max-width: 900px) {
  .stats-grid { grid-template-columns: repeat(2, 1fr); }
  .quick-grid { grid-template-columns: repeat(3, 1fr); }
  .welcome-section { flex-direction: column; align-items: flex-start; gap: 12px; }
}
@media (max-width: 480px) {
  .stats-grid { grid-template-columns: 1fr; }
  .quick-grid { grid-template-columns: repeat(2, 1fr); }
}
</style>