// ─── Backend Switch ──────────────────────────────────
// 支持运行时在 Python (Django) 与 Go 后端之间切换
// localStorage key: 'backend-mode'  value: 'python' | 'go'
const PYTHON_API = import.meta.env.VITE_API_BASE_URL || '/api/v1'
const GO_API = import.meta.env.VITE_GO_API_BASE_URL || '/go-api/v1'

export type BackendMode = 'python' | 'go'

/** 从 localStorage 读取当前后端模式 */
export function getBackendMode(): BackendMode {
  const stored = localStorage.getItem('backend-mode')
  if (stored === 'go' || stored === 'python') return stored
  return 'python'
}

/** 获取当前后端的 API base URL */
export function getApiBase(): string {
  return getBackendMode() === 'go' ? GO_API : PYTHON_API
}

/** 切换后端模式，返回新的 base URL */
export function switchBackend(mode: BackendMode): string {
  localStorage.setItem('backend-mode', mode)
  return mode === 'go' ? GO_API : PYTHON_API
}

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const token = localStorage.getItem('event.token')
  const res = await fetch(`${getApiBase()}${path}`, {
    headers: {
      'Content-Type': 'application/json',
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...options?.headers,
    },
    ...options,
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }))
    throw new Error(err.detail || res.statusText)
  }
  return res.json()
}

// ── 统一认证（SSO，方式二：直连 JWKS 验签）────────────────────
// auth 相关请求始终走 Python 后端（Go 后端无 auth 端点）
export interface MeInfo {
  username: string
  is_active: boolean
  auth_source: string
}
export async function fetchMe(): Promise<MeInfo> {
  const token = localStorage.getItem('event.token')
  const res = await fetch(`${PYTHON_API}/auth/me`, {
    headers: {
      'Content-Type': 'application/json',
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    },
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }))
    throw new Error(err.detail || res.statusText)
  }
  return res.json()
}

export function fetchCurrentUser(): Promise<MeInfo> {
  // auth 始终走 Python 后端（Go 后端无 auth 端点）
  return fetchMe()
}

export interface Event {
  id: string
  event_type: string
  source: string
  detail_type: string
  resource_id: string
  raw_payload: Record<string, unknown>
  status: 'pending' | 'processing' | 'completed' | 'failed' | 'dlq'
  trace_id: string
  retry_count: number
  max_retries: number
  handler: string
  worker_id: string
  error_message: string
  received_at: string
  processed_at: string | null
}

export interface EventLog {
  id: number
  action: string
  detail: Record<string, unknown>
  created_at: string
}

export interface EventListResponse {
  items: Event[]
  total: number
  page: number
  page_size: number
}

export interface Stats {
  total: number
  by_status: Record<string, number>
  success_rate: number
  avg_duration: number | null
  p99_duration: number | null
  queue_depth: number
}

export interface EventCreatePayload {
  event_type: string
  source?: string
  detail_type?: string
  resource_id?: string
  raw_payload?: Record<string, unknown>
  max_retries?: number
}

// ─── Top Words 兼容工具 ─────────────────────────
// Python 后端返回 [["word", count], ...]（数组数组）
// Go 后端返回 [{"word": "...", "count": N}, ...]（对象数组）
// 统一归一化为 { word, count }，避免解构崩溃
export function normalizeTopWord(item: unknown): { word: string; count: number } {
  if (Array.isArray(item)) {
    return { word: String(item[0] ?? ''), count: Number(item[1] ?? 0) }
  }
  if (item && typeof item === 'object') {
    const obj = item as Record<string, unknown>
    return {
      word: String(obj.word ?? ''),
      count: Number(obj.count ?? 0),
    }
  }
  return { word: String(item ?? ''), count: 0 }
}

// ─── API Functions ──────────────────────────────

export const eventsApi = {
  list: (params?: { page?: number; page_size?: number; status?: string; search?: string; search_field?: string }) => {
    const qs = new URLSearchParams()
    if (params?.page) qs.set('page', String(params.page))
    if (params?.page_size) qs.set('page_size', String(params.page_size))
    if (params?.status) qs.set('status', params.status)
    if (params?.search) qs.set('search', params.search)
    if (params?.search_field) qs.set('search_field', params.search_field)
    return request<EventListResponse>(`/events?${qs}`)
  },

  get: (id: string) => request<Event>(`/events/${id}`),

  getLogs: (id: string) => request<EventLog[]>(`/events/${id}/logs`),

  create: (payload: EventCreatePayload) =>
    request<Event>('/events', {
      method: 'POST',
      body: JSON.stringify(payload),
    }),

  retry: (id: string) =>
    request<Event>(`/events/${id}/retry`, {
      method: 'POST',
      body: JSON.stringify({ force: false }),
    }),

  replayDlq: (eventIds: string[]) =>
    request<{ replayed: number }>('/events/dlq/replay', {
      method: 'POST',
      body: JSON.stringify({ event_ids: eventIds }),
    }),
}

export const statsApi = {
  get: () => request<Stats>('/stats'),
  queues: () => request<Array<{ name: string; label: string; depth: number }>>('/stats/queues'),
  workers: () => request<{ total: number; online: number; active_tasks: number; queued_tasks: number; workers: Array<{ id: string; status: string; hostname: string }> }>('/stats/workers'),
  throughput: () => request<Array<{ hour: string; total: number; completed: number; failed: number; other: number }>>('/stats/throughput'),
  recentFailures: (limit = 5) => request<Array<{ id: string; event_type: string; status: string; error_message: string; retry_count: number; max_retries: number; received_at: string }>>(`/stats/recent-failures?limit=${limit}`),
}

export const handlersApi = {
  list: () => request<Array<{ id: number; name: string; event_type_pattern: string }>>('/handlers'),
  listTypes: () => request<Array<{ category: string; icon: string; pattern: string; description: string; handler: string }>>('/handlers/event-types'),
}

export interface DocInfo {
  filename: string
  title: string
  description: string
  size: number
  modified_at: string
}

export const docsApi = {
  list: () => request<DocInfo[]>('/docs'),
}
