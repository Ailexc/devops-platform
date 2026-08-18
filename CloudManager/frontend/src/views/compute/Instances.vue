<template>
  <div class="instances-page">
    <!-- 页面标题 -->
    <div class="page-header fade-in">
      <div class="header-content">
        <h1 class="page-title">云主机管理</h1>
        <p class="page-subtitle">管理和监控您的云服务器实例</p>
      </div>
      <div class="header-actions">
        <button class="action-btn" @click="fetchResources">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M23 4v6h-6M1 20v-6h6"></path>
            <path d="M3.51 9a9 9 0 0 1 14.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0 0 20.49 15"></path>
          </svg>
          <span>刷新</span>
        </button>
        <button class="action-btn primary" @click="handleCreate">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M12 5v14M5 12h14"></path>
          </svg>
          <span>申请主机</span>
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
          placeholder="搜索主机名/ID..." 
          class="search-input"
          @keyup.enter="fetchResources"
        />
      </div>
      
      <div class="filter-group">
        <label class="filter-label">状态</label>
        <select v-model="filters.status" class="filter-select" @change="fetchResources">
          <option value="">全部状态</option>
          <option v-for="s in statuses" :key="s" :value="s">{{ statusLabels[s] || s }}</option>
        </select>
      </div>
      
      <div class="filter-group">
        <label class="filter-label">地域</label>
        <select v-model="globalStore.region" class="filter-select" @change="fetchResources">
          <option value="">全部地域</option>
          <option v-for="r in regions" :key="r" :value="r">{{ r }}</option>
        </select>
      </div>
    </div>

    <!-- 数据表格 -->
    <div class="table-card fade-in delay-2">
      <div class="table-wrapper">
        <table class="data-table">
          <thead>
            <tr>
              <th>资源名称</th>
              <th>资源ID</th>
              <th>地域</th>
              <th>规格</th>
              <th>状态</th>
              <th>云账号</th>
              <th>创建时间</th>
              <th>操作</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="record in resources" :key="record.id">
              <td>
                <a class="resource-link" @click="handleDetail(record)">{{ record.resource_name }}</a>
              </td>
              <td class="mono-text">{{ record.cloud_resource_id }}</td>
              <td>{{ record.region }}</td>
              <td>{{ record.spec || '-' }}</td>
              <td>
                <span class="status-badge" :class="record.status">
                  <span class="status-dot"></span>
                  {{ statusLabels[record.status] || record.status }}
                </span>
              </td>
              <td>{{ record.account_name }}</td>
              <td>{{ record.created_at }}</td>
              <td>
                <div class="action-group">
                  <button 
                    v-if="record.status === 'stopped'" 
                    class="action-btn-sm success"
                    @click="handleAction('start', record)"
                  >
                    启动
                  </button>
                  <button 
                    v-if="record.status === 'running'" 
                    class="action-btn-sm danger"
                    @click="handleAction('stop', record)"
                  >
                    停止
                  </button>
                  <button 
                    class="action-btn-sm"
                    :disabled="record.status !== 'running'"
                    @click="handleAction('resize', record)"
                  >
                    变更
                  </button>
                  <button 
                    class="action-btn-sm danger"
                    @click="handleAction('release', record)"
                  >
                    下线
                  </button>
                </div>
              </td>
            </tr>
            <tr v-if="!resources.length && !loading">
              <td colspan="8">
                <div class="empty-state">
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z"></path>
                  </svg>
                  <span>暂无数据</span>
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
            @click="filters.page--; fetchResources()"
          >
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M15 18l-6-6 6-6"></path>
            </svg>
          </button>
          <span class="page-current">{{ filters.page }}</span>
          <button 
            class="page-btn"
            :disabled="filters.page * filters.page_size >= total"
            @click="filters.page++; fetchResources()"
          >
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M9 18l6-6-6-6"></path>
            </svg>
          </button>
        </div>
        <select v-model="filters.page_size" class="page-size-select" @change="fetchResources">
          <option :value="10">10条/页</option>
          <option :value="20">20条/页</option>
          <option :value="50">50条/页</option>
        </select>
      </div>
    </div>

    <!-- 申请主机弹窗 -->
    <div v-if="showCreateModal" class="modal-overlay" @click.self="showCreateModal = false">
      <div class="modal-content">
        <div class="modal-header">
          <h3>申请云主机</h3>
          <button class="modal-close" @click="showCreateModal = false">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M18 6L6 18M6 6l12 12"></path>
            </svg>
          </button>
        </div>
        <div class="modal-body">
          <div class="form-group">
            <label class="form-label">主机名称 <span class="required">*</span></label>
            <input v-model="createForm.name" type="text" class="form-input" placeholder="请输入主机名称" />
          </div>
          
          <div class="form-row">
            <div class="form-group">
              <label class="form-label">地域 <span class="required">*</span></label>
              <select v-model="createForm.region" class="form-select">
                <option v-for="r in regions" :key="r" :value="r">{{ r }}</option>
              </select>
            </div>
            <div class="form-group">
              <label class="form-label">规格 <span class="required">*</span></label>
              <select v-model="createForm.spec" class="form-select">
                <option v-for="s in specs" :key="s" :value="s">{{ s }}</option>
              </select>
            </div>
          </div>
          
          <div class="form-row">
            <div class="form-group">
              <label class="form-label">CPU (核)</label>
              <input v-model.number="createForm.cpu" type="number" class="form-input" min="1" max="64" />
            </div>
            <div class="form-group">
              <label class="form-label">内存 (GB)</label>
              <input v-model.number="createForm.memory_gb" type="number" class="form-input" min="1" max="256" />
            </div>
          </div>
          
          <div class="form-group">
            <label class="form-label">操作系统</label>
            <select v-model="createForm.os" class="form-select">
              <option value="ubuntu-22.04">Ubuntu 22.04</option>
              <option value="centos-7.9">CentOS 7.9</option>
              <option value="windows-2022">Windows Server 2022</option>
            </select>
          </div>
        </div>
        <div class="modal-footer">
          <button class="btn-secondary" @click="showCreateModal = false">取消</button>
          <button class="btn-primary" @click="submitCreate">提交申请</button>
        </div>
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
import { message, Modal } from 'ant-design-vue'
import { resourceApi, ticketApi } from '@/api'
import type { Resource } from '@/types'
import { useGlobalStore } from '@/stores/global'

const router = useRouter()
const globalStore = useGlobalStore()
const loading = ref(false)
const resources = ref<Resource[]>([])
const total = ref(0)
const showCreateModal = ref(false)

const filters = reactive({
  page: 1,
  page_size: 20,
  resource_type: 'instance',
  status: '',
  search: '',
})

const createForm = reactive({
  name: '',
  region: 'cn-hangzhou',
  spec: 't3.medium',
  cpu: 4,
  memory_gb: 8,
  os: 'ubuntu-22.04',
})

const regions = ['cn-hangzhou', 'cn-shanghai', 'cn-beijing', 'us-east-1']
const specs = ['t3.medium', 't3.large', 't3.xlarge', 'ecs.g6.large', 'ecs.g6.xlarge', 'ecs.g6.2xlarge']
const statuses = ['running', 'stopped', 'pending', 'unknown']

const statusLabels: Record<string, string> = {
  running: '运行中',
  stopped: '已停止',
  pending: '等待中',
  unknown: '未知',
}

async function fetchResources() {
  loading.value = true
  try {
    const params: any = { ...filters }
    params.region = globalStore.region || undefined
    params.account = globalStore.accountId || undefined
    Object.keys(params).forEach((key) => {
      if (!params[key]) delete params[key]
    })
    const { data } = await resourceApi.list(params)
    resources.value = data.results
    total.value = data.count
  } catch {
    message.error('获取资源列表失败')
  } finally {
    loading.value = false
  }
}

function handleDetail(record: Resource) {
  router.push(`/resources/${record.id}`)
}

function handleCreate() {
  showCreateModal.value = true
}

async function submitCreate() {
  try {
    await ticketApi.create({
      ticket_type: 'create_instance',
      title: `申请主机 - ${createForm.name}`,
      provider_type: 'mock',
      resource_name: createForm.name,
      request_content: { ...createForm },
    })
    message.success('工单已提交')
    showCreateModal.value = false
    fetchResources()
  } catch {
    message.error('提交失败')
  }
}

function handleAction(action: string, record: Resource) {
  const actionNames: Record<string, string> = {
    start: '启动',
    stop: '停止',
    resize: '变更规格',
    release: '下线',
  }
  Modal.confirm({
    title: `确认${actionNames[action]}？`,
    content: `确定要${actionNames[action]}资源 ${record.resource_name} (${record.cloud_resource_id}) 吗？`,
    onOk: async () => {
      try {
        await ticketApi.create({
          ticket_type: action,
          title: `${actionNames[action]} - ${record.resource_name}`,
          provider_type: record.provider_type,
          resource_id: record.cloud_resource_id,
          resource_name: record.resource_name,
          request_content: { spec: createForm.spec },
        })
        message.success('工单已提交')
        fetchResources()
      } catch {
        message.error('操作失败')
      }
    },
  })
}

onMounted(fetchResources)
</script>

<style scoped>
.instances-page {
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

.action-btn.primary {
  background: linear-gradient(135deg, var(--cm-color-primary-600) 0%, var(--cm-color-primary-700) 100%);
  border-color: transparent;
  color: white;
  box-shadow: 0 4px 12px rgba(124, 58, 237, 0.3);
}

.action-btn.primary:hover {
  transform: translateY(-1px);
  box-shadow: 0 6px 16px rgba(124, 58, 237, 0.4);
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

.resource-link {
  color: var(--cm-color-primary-600);
  font-weight: var(--cm-font-medium);
  cursor: pointer;
  transition: color var(--cm-transition-fast);
}

.resource-link:hover {
  color: var(--cm-color-primary-700);
  text-decoration: underline;
}

.mono-text {
  font-family: var(--cm-font-mono);
  font-size: var(--cm-text-xs);
  color: var(--cm-text-secondary);
}

/* 状态标签 */
.status-badge {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 4px 10px;
  border-radius: var(--cm-radius-full);
  font-size: var(--cm-text-xs);
  font-weight: var(--cm-font-medium);
}

.status-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
}

.status-badge.running {
  background: rgba(16, 185, 129, 0.1);
  color: #059669;
}

.status-badge.running .status-dot {
  background: #10B981;
  box-shadow: 0 0 6px #10B981;
}

.status-badge.stopped {
  background: rgba(107, 114, 128, 0.1);
  color: #4B5563;
}

.status-badge.stopped .status-dot {
  background: #6B7280;
}

.status-badge.pending {
  background: rgba(245, 158, 11, 0.1);
  color: #D97706;
}

.status-badge.pending .status-dot {
  background: #F59E0B;
  animation: pulse 1.5s infinite;
}

.status-badge.unknown {
  background: rgba(107, 114, 128, 0.1);
  color: #6B7280;
}

.status-badge.unknown .status-dot {
  background: #9CA3AF;
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.5; }
}

/* 操作按钮 */
.action-group {
  display: flex;
  gap: 6px;
}

.action-btn-sm {
  padding: 4px 10px;
  font-size: var(--cm-text-xs);
  font-weight: var(--cm-font-medium);
  font-family: inherit;
  background: white;
  border: 1px solid var(--cm-border-default);
  border-radius: var(--cm-radius-sm);
  color: var(--cm-text-secondary);
  cursor: pointer;
  transition: all var(--cm-transition-fast);
}

.action-btn-sm:hover:not(:disabled) {
  border-color: var(--cm-color-primary-300);
  color: var(--cm-color-primary-600);
}

.action-btn-sm:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.action-btn-sm.success {
  background: rgba(16, 185, 129, 0.1);
  border-color: rgba(16, 185, 129, 0.3);
  color: #059669;
}

.action-btn-sm.success:hover {
  background: rgba(16, 185, 129, 0.2);
}

.action-btn-sm.danger {
  background: rgba(239, 68, 68, 0.1);
  border-color: rgba(239, 68, 68, 0.3);
  color: #DC2626;
}

.action-btn-sm.danger:hover {
  background: rgba(239, 68, 68, 0.2);
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

/* 弹窗 */
.modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.5);
  backdrop-filter: blur(4px);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  animation: fadeIn 0.2s ease;
}

@keyframes fadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}

.modal-content {
  width: 100%;
  max-width: 560px;
  background: white;
  border-radius: var(--cm-radius-xl);
  box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.25);
  animation: slideUp 0.3s ease;
}

@keyframes slideUp {
  from {
    opacity: 0;
    transform: translateY(20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.modal-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 20px 24px;
  border-bottom: 1px solid var(--cm-border-default);
}

.modal-header h3 {
  font-size: var(--cm-text-lg);
  font-weight: var(--cm-font-semibold);
  color: var(--cm-text-primary);
  margin: 0;
}

.modal-close {
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: transparent;
  border: none;
  border-radius: var(--cm-radius-md);
  color: var(--cm-text-tertiary);
  cursor: pointer;
  transition: all var(--cm-transition-fast);
}

.modal-close:hover {
  background: var(--cm-bg-tertiary);
  color: var(--cm-text-primary);
}

.modal-close svg {
  width: 20px;
  height: 20px;
}

.modal-body {
  padding: 24px;
}

.modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  padding: 16px 24px;
  border-top: 1px solid var(--cm-border-default);
}

/* 表单 */
.form-group {
  margin-bottom: 20px;
}

.form-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
}

.form-label {
  display: block;
  font-size: var(--cm-text-sm);
  font-weight: var(--cm-font-medium);
  color: var(--cm-text-primary);
  margin-bottom: 8px;
}

.required {
  color: var(--cm-color-error);
}

.form-input,
.form-select {
  width: 100%;
  padding: 10px 12px;
  font-size: var(--cm-text-sm);
  font-family: inherit;
  color: var(--cm-text-primary);
  background: white;
  border: 1px solid var(--cm-border-default);
  border-radius: var(--cm-radius-md);
  transition: all var(--cm-transition-fast);
}

.form-input:focus,
.form-select:focus {
  outline: none;
  border-color: var(--cm-border-focus);
  box-shadow: 0 0 0 3px rgba(139, 92, 246, 0.1);
}

.form-select {
  appearance: none;
  background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='16' height='16' viewBox='0 0 24 24' fill='none' stroke='%236B7280' stroke-width='2'%3E%3Cpath d='M6 9l6 6 6-6'%3E%3C/path%3E%3C/svg%3E");
  background-repeat: no-repeat;
  background-position: right 10px center;
  padding-right: 36px;
}

.btn-secondary,
.btn-primary {
  padding: 10px 20px;
  font-size: var(--cm-text-sm);
  font-weight: var(--cm-font-medium);
  font-family: inherit;
  border-radius: var(--cm-radius-md);
  cursor: pointer;
  transition: all var(--cm-transition-fast);
}

.btn-secondary {
  background: white;
  border: 1px solid var(--cm-border-default);
  color: var(--cm-text-primary);
}

.btn-secondary:hover {
  background: var(--cm-bg-tertiary);
}

.btn-primary {
  background: linear-gradient(135deg, var(--cm-color-primary-600) 0%, var(--cm-color-primary-700) 100%);
  border: none;
  color: white;
  box-shadow: 0 4px 12px rgba(124, 58, 237, 0.3);
}

.btn-primary:hover {
  transform: translateY(-1px);
  box-shadow: 0 6px 16px rgba(124, 58, 237, 0.4);
}

/* 抽屉 */
.drawer-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.5);
  backdrop-filter: blur(4px);
  z-index: 1000;
  animation: fadeIn 0.2s ease;
}

.drawer-content {
  position: absolute;
  right: 0;
  top: 0;
  bottom: 0;
  width: 100%;
  max-width: 500px;
  background: white;
  box-shadow: -10px 0 30px rgba(0, 0, 0, 0.1);
  animation: slideLeft 0.3s ease;
}

@keyframes slideLeft {
  from {
    transform: translateX(100%);
  }
  to {
    transform: translateX(0);
  }
}

.drawer-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 20px 24px;
  border-bottom: 1px solid var(--cm-border-default);
}

.drawer-header h3 {
  font-size: var(--cm-text-lg);
  font-weight: var(--cm-font-semibold);
  color: var(--cm-text-primary);
  margin: 0;
}

.drawer-close {
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: transparent;
  border: none;
  border-radius: var(--cm-radius-md);
  color: var(--cm-text-tertiary);
  cursor: pointer;
  transition: all var(--cm-transition-fast);
}

.drawer-close:hover {
  background: var(--cm-bg-tertiary);
  color: var(--cm-text-primary);
}

.drawer-close svg {
  width: 20px;
  height: 20px;
}

.drawer-body {
  padding: 24px;
  overflow-y: auto;
  max-height: calc(100vh - 80px);
}

.detail-item {
  display: flex;
  align-items: flex-start;
  padding: 12px 0;
  border-bottom: 1px solid var(--cm-border-default);
}

.detail-item:last-child {
  border-bottom: none;
}

.detail-item.full {
  flex-direction: column;
}

.detail-label {
  width: 100px;
  font-size: var(--cm-text-sm);
  color: var(--cm-text-secondary);
  flex-shrink: 0;
}

.detail-value {
  font-size: var(--cm-text-sm);
  color: var(--cm-text-primary);
  font-weight: var(--cm-font-medium);
}

.detail-value.mono {
  font-family: var(--cm-font-mono);
  font-size: var(--cm-text-xs);
}

.detail-pre {
  width: 100%;
  margin-top: 8px;
  padding: 12px;
  background: var(--cm-bg-tertiary);
  border-radius: var(--cm-radius-md);
  font-family: var(--cm-font-mono);
  font-size: var(--cm-text-xs);
  white-space: pre-wrap;
  word-break: break-all;
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
  
  .form-row {
    grid-template-columns: 1fr;
  }
  
  .pagination {
    flex-direction: column;
    gap: 12px;
  }
}

/* 暗色模式 */
@media (prefers-color-scheme: dark) {
  .modal-content,
  .drawer-content {
    background: var(--cm-bg-secondary);
  }
  
  .form-input,
  .form-select,
  .filter-select,
  .page-size-select {
    background-color: rgba(0, 0, 0, 0.2);
    border-color: rgba(255, 255, 255, 0.1);
    color: white;
  }
  
  .action-btn,
  .action-btn-sm,
  .page-btn,
  .btn-secondary {
    background: var(--cm-bg-tertiary);
    border-color: rgba(255, 255, 255, 0.1);
  }
}
</style>
