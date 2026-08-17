import axios from 'axios'

// ── 后端实现切换（同一契约，可配置后端）──────────────────────────
// python: Django + Celery（当前同源反代）
// go:     Gin + asynq（通过 VITE_GO_API_BASE 指定，默认本地 8080）
const BACKENDS = {
  python: {
    label: 'Python (Django + Celery)',
    base: '/api/v1',
  },
  go: {
    label: 'Go (Gin + asynq)',
    base: import.meta.env.VITE_GO_API_BASE || '/go-api/api/v1',
  },
}

const STORAGE_KEY = 'cmdb.backend'

export function getCurrentBackend() {
  const key = localStorage.getItem(STORAGE_KEY)
  return BACKENDS[key] ? key : 'python'
}

export function getBackendLabel(key) {
  return BACKENDS[key]?.label || BACKENDS.python.label
}

function resolveBase() {
  return BACKENDS[getCurrentBackend()].base
}

export function switchBackend(key) {
  if (!BACKENDS[key]) return
  localStorage.setItem(STORAGE_KEY, key)
  api.defaults.baseURL = BACKENDS[key].base
}

const api = axios.create({
  baseURL: resolveBase(),
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
})

// ── Dashboard ──────────────────────────────────────────────────────

export function fetchDashboardStats() {
  return api.get('/dashboard/stats/')
}

export function fetchWorkers() {
  return api.get('/dashboard/workers/')
}

export function fetchResourceHealth() {
  return api.get('/dashboard/resource-health/')
}

export function fetchTaskTrend() {
  return api.get('/dashboard/task-trend/')
}

export function fetchHealthRanking() {
  return api.get('/dashboard/health-ranking/')
}

export function fetchCurrentRunning() {
  return api.get('/dashboard/current/')
}

export function fetchRecentEvents() {
  return api.get('/dashboard/recent-events/')
}

export function fetchResourceBreakdown() {
  return api.get('/dashboard/resource-breakdown/')
}

export function fetchAWSResources() {
  return api.get('/dashboard/aws-resources/')
}

// ── Tasks ──────────────────────────────────────────────────────────

export function fetchTaskTree() {
  return api.get('/tasks/tree/')
}

export function executeTask(params) {
  return api.post('/tasks/execute/', params)
}

// 设置/取消 cron（写调度层 PeriodicTask）
export function updateTaskSchedule(name, cron) {
  return api.put('/tasks/schedule/', { name, cron })
}

export function fetchTaskLocks() {
  return api.get('/tasks/locks/')
}

export function previewTask(params) {
  return api.post('/tasks/preview/', params)
}

export function runTestTask(taskName) {
  return api.post('/tasks/test/run/', { task: taskName })
}

export function getTestTaskStatus(taskId) {
  return api.get(`/tasks/test/status/${taskId}/`)
}

export function previewTestFile(filePath) {
  return api.get('/tasks/test/file/', { params: { path: filePath } })
}

// ── Config ─────────────────────────────────────────────────────────

export function fetchRegionConfig() {
  return api.get('/config/regions/')
}

export function updateRegionConfig(data) {
  return api.put('/config/regions/', data)
}

export function fetchAccounts() {
  return api.get('/config/accounts/')
}

// ── History ─────────────────────────────────────────────────────────

export function fetchHistory(params = {}) {
  return api.get('/history/', { params })
}

export function fetchHistoryDetail(recordId) {
  return api.get(`/history/${recordId}/`)
}

export function retryHistory(recordId) {
  return api.post(`/history/${recordId}/retry/`)
}

// ── Docs ───────────────────────────────────────────────────────────

export function fetchDocList() {
  return api.get('/docs/')
}

export function fetchDocContent(filename) {
  return api.get(`/docs/${encodeURIComponent(filename)}`)
}

export default api
