<template>
  <div class="ticket-page">
    <!-- 页面标题 -->
    <div class="page-header fade-in">
      <div class="header-content">
        <h1 class="page-title">工单中心</h1>
        <p class="page-subtitle">管理和跟踪所有运维工单</p>
      </div>
      <div class="header-actions">
        <button class="action-btn" @click="fetchTickets">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M23 4v6h-6M1 20v-6h6"></path>
            <path d="M3.51 9a9 9 0 0 1 14.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0 0 20.49 15"></path>
          </svg>
          <span>刷新</span>
        </button>
      </div>
    </div>

    <!-- 筛选栏 -->
    <div class="filter-bar fade-in delay-1">
      <div class="search-box">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <circle cx="11" cy="11" r="8"></circle>
          <path d="M21 21l-4.35-4.35"></path>
        </svg>
        <input 
          v-model="filters.search" 
          type="text" 
          placeholder="搜索工单号/标题..." 
          class="search-input"
          @keyup.enter="fetchTickets"
        />
      </div>
      
      <div class="filter-group">
        <label class="filter-label">状态</label>
        <select v-model="filters.status" class="filter-select" @change="fetchTickets">
          <option value="">全部状态</option>
          <option value="pending">待审批</option>
          <option value="executing">待执行</option>
          <option value="running">执行中</option>
          <option value="success">成功</option>
          <option value="failed">失败</option>
          <option value="rejected">已驳回</option>
        </select>
      </div>
    </div>

    <!-- 数据表格 -->
    <div class="table-card fade-in delay-2">
      <div class="table-wrapper">
        <table class="data-table">
          <thead>
            <tr>
              <th>工单号</th>
              <th>类型</th>
              <th>标题</th>
              <th>状态</th>
              <th>申请人</th>
              <th>资源</th>
              <th>创建时间</th>
              <th>操作</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="record in tickets" :key="record.id">
              <td>
                <a class="ticket-link" @click="handleDetail(record)">{{ record.ticket_no }}</a>
              </td>
              <td>{{ record.ticket_type_display }}</td>
              <td class="title-cell">{{ record.title }}</td>
              <td>
                <span class="status-badge" :class="record.status">
                  {{ record.status_display }}
                </span>
              </td>
              <td>{{ record.applicant }}</td>
              <td class="resource-cell">{{ record.resource_name || '-' }}</td>
              <td>{{ record.created_at }}</td>
              <td>
                <button class="action-btn-sm" @click="handleDetail(record)">
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"></path>
                    <circle cx="12" cy="12" r="3"></circle>
                  </svg>
                  详情
                </button>
              </td>
            </tr>
            <tr v-if="!tickets.length && !loading">
              <td colspan="8">
                <div class="empty-state">
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8l-6-6z"></path>
                    <path d="M14 2v6h6"></path>
                  </svg>
                  <span>暂无工单</span>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
      
      <!-- 分页 -->
      <div class="pagination">
        <span class="page-info">共 {{ total }} 条</span>
        <div class="page-buttons">
          <button 
            class="page-btn" 
            :disabled="filters.page <= 1"
            @click="filters.page--; fetchTickets()"
          >
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M15 18l-6-6 6-6"></path>
            </svg>
          </button>
          <span class="page-current">{{ filters.page }}</span>
          <button 
            class="page-btn"
            :disabled="filters.page * filters.page_size >= total"
            @click="filters.page++; fetchTickets()"
          >
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M9 18l6-6-6-6"></path>
            </svg>
          </button>
        </div>
        <select v-model="filters.page_size" class="page-size-select" @change="fetchTickets">
          <option :value="10">10条/页</option>
          <option :value="20">20条/页</option>
          <option :value="50">50条/页</option>
        </select>
      </div>
    </div>

    <!-- 加载状态 -->
    <div v-if="loading" class="loading-overlay">
      <div class="loading-spinner"></div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { message } from 'ant-design-vue'
import { ticketApi } from '@/api'
import type { TicketOrder } from '@/types'

const router = useRouter()
const loading = ref(false)
const tickets = ref<TicketOrder[]>([])
const total = ref(0)

const filters = reactive({
  page: 1,
  page_size: 20,
  status: '',
  ticket_type: '',
  search: '',
})

async function fetchTickets() {
  loading.value = true
  try {
    const params: any = { ...filters }
    Object.keys(params).forEach((key) => {
      if (!params[key]) delete params[key]
    })
    const { data } = await ticketApi.list(params)
    tickets.value = data.results
    total.value = data.count
  } catch {
    message.error('获取工单列表失败')
  } finally {
    loading.value = false
  }
}

function handleDetail(record: TicketOrder) {
  router.push(`/ticket/detail/${record.id}`)
}

onMounted(fetchTickets)
</script>

<style scoped>
.ticket-page {
  max-width: 1400px;
  margin: 0 auto;
}

/* 页面标题 */
.page-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 24px;
}

.page-title {
  font-size: var(--cm-text-3xl);
  font-weight: var(--cm-font-bold);
  color: var(--cm-text-primary);
  margin: 0;
}

.page-subtitle {
  font-size: var(--cm-text-base);
  color: var(--cm-text-secondary);
  margin: 8px 0 0;
}

.header-actions {
  display: flex;
  gap: 12px;
}

.action-btn {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 16px;
  background: white;
  border: 1px solid var(--cm-border-default);
  border-radius: var(--cm-radius-md);
  font-size: var(--cm-text-sm);
  font-weight: var(--cm-font-medium);
  font-family: inherit;
  color: var(--cm-text-primary);
  cursor: pointer;
  transition: all var(--cm-transition-fast);
}

.action-btn:hover {
  border-color: var(--cm-border-hover);
  background: var(--cm-bg-tertiary);
}

.action-btn svg {
  width: 18px;
  height: 18px;
}

/* 筛选栏 */
.filter-bar {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 16px 20px;
  background: var(--cm-glass-bg);
  backdrop-filter: var(--cm-glass-blur);
  border: 1px solid var(--cm-glass-border);
  border-radius: var(--cm-radius-xl);
  margin-bottom: 20px;
}

.search-box {
  display: flex;
  align-items: center;
  gap: 8px;
  flex: 1;
  max-width: 320px;
  padding: 8px 12px;
  background: white;
  border: 1px solid var(--cm-border-default);
  border-radius: var(--cm-radius-md);
  transition: all var(--cm-transition-fast);
}

.search-box:focus-within {
  border-color: var(--cm-border-focus);
  box-shadow: 0 0 0 3px rgba(139, 92, 246, 0.1);
}

.search-box svg {
  width: 18px;
  height: 18px;
  color: var(--cm-text-tertiary);
  flex-shrink: 0;
}

.search-input {
  flex: 1;
  border: none;
  outline: none;
  font-size: var(--cm-text-sm);
  font-family: inherit;
  color: var(--cm-text-primary);
  background: transparent;
}

.search-input::placeholder {
  color: var(--cm-text-tertiary);
}

.filter-group {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.filter-label {
  font-size: var(--cm-text-xs);
  font-weight: var(--cm-font-medium);
  color: var(--cm-text-secondary);
}

.filter-select {
  padding: 8px 32px 8px 12px;
  font-size: var(--cm-text-sm);
  font-family: inherit;
  color: var(--cm-text-primary);
  background: white url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='16' height='16' viewBox='0 0 24 24' fill='none' stroke='%236B7280' stroke-width='2'%3E%3Cpath d='M6 9l6 6 6-6'%3E%3C/path%3E%3C/svg%3E") no-repeat right 8px center;
  border: 1px solid var(--cm-border-default);
  border-radius: var(--cm-radius-md);
  cursor: pointer;
  transition: all var(--cm-transition-fast);
  appearance: none;
}

.filter-select:hover {
  border-color: var(--cm-border-hover);
}

.filter-select:focus {
  outline: none;
  border-color: var(--cm-border-focus);
  box-shadow: 0 0 0 3px rgba(139, 92, 246, 0.1);
}

/* 表格卡片 */
.table-card {
  background: var(--cm-glass-bg);
  backdrop-filter: var(--cm-glass-blur);
  border: 1px solid var(--cm-glass-border);
  border-radius: var(--cm-radius-xl);
  box-shadow: var(--cm-shadow-glass);
  overflow: hidden;
}

.table-wrapper {
  overflow-x: auto;
}

.data-table {
  width: 100%;
  border-collapse: collapse;
}

.data-table th {
  padding: 14px 16px;
  text-align: left;
  font-size: var(--cm-text-xs);
  font-weight: var(--cm-font-semibold);
  color: var(--cm-text-secondary);
  text-transform: uppercase;
  letter-spacing: 0.05em;
  background: rgba(124, 58, 237, 0.03);
  border-bottom: 1px solid var(--cm-border-default);
}

.data-table td {
  padding: 14px 16px;
  font-size: var(--cm-text-sm);
  color: var(--cm-text-primary);
  border-bottom: 1px solid rgba(124, 58, 237, 0.05);
}

.data-table tbody tr {
  transition: background var(--cm-transition-fast);
}

.data-table tbody tr:hover {
  background: rgba(124, 58, 237, 0.02);
}

.data-table tbody tr:last-child td {
  border-bottom: none;
}

.ticket-link {
  color: var(--cm-color-primary-600);
  font-weight: var(--cm-font-medium);
  cursor: pointer;
  transition: color var(--cm-transition-fast);
}

.ticket-link:hover {
  color: var(--cm-color-primary-700);
  text-decoration: underline;
}

.title-cell {
  max-width: 250px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.resource-cell {
  max-width: 180px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  color: var(--cm-text-secondary);
}

/* 状态标签 */
.status-badge {
  display: inline-flex;
  align-items: center;
  padding: 4px 10px;
  border-radius: var(--cm-radius-full);
  font-size: var(--cm-text-xs);
  font-weight: var(--cm-font-medium);
}

.status-badge.pending {
  background: rgba(245, 158, 11, 0.1);
  color: #D97706;
}

.status-badge.approving,
.status-badge.running {
  background: rgba(59, 130, 246, 0.1);
  color: #2563EB;
}

.status-badge.executing {
  background: rgba(139, 92, 246, 0.1);
  color: #7C3AED;
}

.status-badge.success {
  background: rgba(16, 185, 129, 0.1);
  color: #059669;
}

.status-badge.failed {
  background: rgba(239, 68, 68, 0.1);
  color: #DC2626;
}

.status-badge.rejected {
  background: rgba(239, 68, 68, 0.1);
  color: #DC2626;
}

.status-badge.cancelled {
  background: rgba(107, 114, 128, 0.1);
  color: #4B5563;
}

/* 操作按钮 */
.action-btn-sm {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 4px 10px;
  font-size: var(--cm-text-xs);
  font-weight: var(--cm-font-medium);
  font-family: inherit;
  background: white;
  border: 1px solid var(--cm-border-default);
  border-radius: var(--cm-radius-sm);
  color: var(--cm-color-primary-600);
  cursor: pointer;
  transition: all var(--cm-transition-fast);
}

.action-btn-sm:hover {
  background: var(--cm-color-primary-50);
  border-color: var(--cm-color-primary-300);
}

.action-btn-sm svg {
  width: 14px;
  height: 14px;
}

/* 空状态 */
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 48px;
  color: var(--cm-text-tertiary);
}

.empty-state svg {
  width: 48px;
  height: 48px;
  margin-bottom: 12px;
  opacity: 0.5;
}

/* 分页 */
.pagination {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 16px;
  border-top: 1px solid var(--cm-border-default);
}

.page-info {
  font-size: var(--cm-text-sm);
  color: var(--cm-text-secondary);
}

.page-buttons {
  display: flex;
  align-items: center;
  gap: 4px;
}

.page-btn {
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: white;
  border: 1px solid var(--cm-border-default);
  border-radius: var(--cm-radius-md);
  color: var(--cm-text-primary);
  cursor: pointer;
  transition: all var(--cm-transition-fast);
}

.page-btn:hover:not(:disabled) {
  border-color: var(--cm-color-primary-300);
  color: var(--cm-color-primary-600);
}

.page-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.page-btn svg {
  width: 16px;
  height: 16px;
}

.page-current {
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--cm-color-primary-600);
  border-radius: var(--cm-radius-md);
  font-size: var(--cm-text-sm);
  font-weight: var(--cm-font-medium);
  color: white;
}

.page-size-select {
  padding: 6px 28px 6px 10px;
  font-size: var(--cm-text-sm);
  font-family: inherit;
  color: var(--cm-text-primary);
  background: white url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='16' height='16' viewBox='0 0 24 24' fill='none' stroke='%236B7280' stroke-width='2'%3E%3Cpath d='M6 9l6 6 6-6'%3E%3C/path%3E%3C/svg%3E") no-repeat right 6px center;
  border: 1px solid var(--cm-border-default);
  border-radius: var(--cm-radius-md);
  cursor: pointer;
  appearance: none;
}

/* 加载状态 */
.loading-overlay {
  position: fixed;
  inset: 0;
  background: rgba(255, 255, 255, 0.8);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 2000;
}

.loading-spinner {
  width: 40px;
  height: 40px;
  border: 3px solid var(--cm-color-gray-200);
  border-top-color: var(--cm-color-primary-600);
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

/* 动画 */
.fade-in {
  animation: fadeInUp 0.5s ease forwards;
  opacity: 0;
}

@keyframes fadeInUp {
  from {
    opacity: 0;
    transform: translateY(15px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.delay-1 { animation-delay: 0.1s; }
.delay-2 { animation-delay: 0.2s; }

/* 响应式 */
@media (max-width: 768px) {
  .page-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 16px;
  }
  
  .filter-bar {
    flex-direction: column;
    align-items: stretch;
  }
  
  .search-box {
    max-width: none;
  }
  
  .pagination {
    flex-direction: column;
    gap: 12px;
  }
}

/* 暗色模式 */
@media (prefers-color-scheme: dark) {
  .action-btn,
  .action-btn-sm,
  .page-btn {
    background: var(--cm-bg-tertiary);
    border-color: rgba(255, 255, 255, 0.1);
  }
  
  .search-box,
  .filter-select,
  .page-size-select {
    background-color: rgba(0, 0, 0, 0.2);
    border-color: rgba(255, 255, 255, 0.1);
    color: white;
  }
}
</style>
