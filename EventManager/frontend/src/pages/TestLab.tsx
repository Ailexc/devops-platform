import { useState, useEffect, useRef, useCallback } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import { getApiBase, normalizeTopWord } from '../api'

async function apiRequest<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${getApiBase()}${path}`, {
    headers: { 'Content-Type': 'application/json', ...options?.headers },
    ...options,
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }))
    throw new Error(err.detail || res.statusText)
  }
  return res.json()
}

// ─── Types ──────────────────────────────────────

interface DemoTask {
  id: string
  name: string
  description: string
  duration: string
  max_count: number
  default_count: number
}

interface TriggerResult {
  task_id: string
  celery_task_id: string
  count: number
  batch_id: string
  message: string
}

interface TaskStatus {
  celery_task_id: string
  state: string
  meta?: {
    current?: number
    total?: number
    status?: string
    step?: string
    step_progress?: string
    elapsed_sec?: number
    error?: string
  }
  result?: {
    success: boolean
    output_file?: string
    output_filename?: string
    total_batches?: number
    total_posts?: number
    total_reports?: number
    event_id?: string
    batch_id?: string
    source_url?: string
    top_words?: [string, number][]
    report_id?: string
    data_points?: number
    metrics?: {
      avg_response_time_ms?: number
      error_rate?: number
      throughput_rps?: number
      p99_latency_ms?: number
    }
  }
  event_ids?: string[]
}

interface RunningTask {
  triggerResult: TriggerResult
  status: TaskStatus
}

// ─── Task Card ──────────────────────────────────

function TaskCard({
  task,
  onTrigger,
  isRunning,
}: {
  task: DemoTask
  onTrigger: (taskId: string, count: number) => void
  isRunning: boolean
}) {
  const [count, setCount] = useState(task.default_count)

  return (
    <div className="bg-white rounded-xl border border-slate-200 overflow-hidden hover:shadow-md transition-shadow">
      <div className="px-5 py-4">
        <div className="flex items-center justify-between mb-2">
          <h3 className="text-base font-semibold text-slate-800">{task.name}</h3>
          <span className="text-xs font-mono bg-slate-100 text-slate-500 px-2 py-1 rounded">
            {task.duration}
          </span>
        </div>
        <p className="text-sm text-slate-500 mb-4">{task.description}</p>

        <div className="flex items-center gap-3">
          <label className="text-sm text-slate-500">数量:</label>
          <div className="flex items-center border border-slate-200 rounded-lg overflow-hidden">
            <button
              onClick={() => setCount(Math.max(1, count - 1))}
              disabled={count <= 1 || isRunning}
              className="px-3 py-1.5 text-slate-500 hover:bg-slate-100 disabled:opacity-30 transition-colors"
            >
              −
            </button>
            <input
              type="number"
              value={count}
              onChange={(e) => {
                const val = parseInt(e.target.value, 10)
                if (!isNaN(val)) {
                  setCount(Math.max(1, Math.min(task.max_count, val)))
                }
              }}
              disabled={isRunning}
              min={1}
              max={task.max_count}
              className="px-2 py-1.5 text-sm font-medium text-slate-700 w-16 text-center border-x border-slate-200 focus:outline-none focus:ring-2 focus:ring-primary-300 disabled:bg-slate-50"
            />
            <button
              onClick={() => setCount(Math.min(task.max_count, count + 1))}
              disabled={count >= task.max_count || isRunning}
              className="px-3 py-1.5 text-slate-500 hover:bg-slate-100 disabled:opacity-30 transition-colors"
            >
              +
            </button>
          </div>
          <span className="text-xs text-slate-400">最多 {task.max_count}</span>
        </div>
      </div>

      <div className="px-5 py-3 bg-slate-50 border-t border-slate-100">
        <button
          onClick={() => onTrigger(task.id, count)}
          disabled={isRunning}
          className="w-full px-4 py-2 bg-primary-500 text-white rounded-lg text-sm font-medium hover:bg-primary-600 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
        >
          {isRunning ? '⏳ 运行中...' : '🚀 触发任务'}
        </button>
      </div>
    </div>
  )
}

// ─── Running Task Panel ──────────────────────────

function RunningTaskPanel({ task }: { task: RunningTask }) {
  const { triggerResult, status } = task
  const taskDef = TASK_MAP[triggerResult.task_id]
  const isComplete = status.state === 'SUCCESS' || status.state === 'FAILURE'
  const isRunning = status.state === 'PROGRESS' || status.state === 'PENDING'
  const [previewData, setPreviewData] = useState<{ filename: string; content: string; size: number } | null>(null)
  const [previewLoading, setPreviewLoading] = useState(false)

  // 获取批次号中的事件列表
  const [batchEvents, setBatchEvents] = useState<any[]>([])
  useEffect(() => {
    if (triggerResult.batch_id) {
      fetch(`${getApiBase()}/events?search=${triggerResult.batch_id}`)
        .then(res => res.json())
        .then(data => {
          if (data?.items) {
            setBatchEvents(data.items)
          }
        })
        .catch(() => {})
    }
  }, [triggerResult.batch_id])

  const handlePreview = async () => {
    const filename = status.result?.output_filename
    if (!filename) return
    setPreviewLoading(true)
    try {
      const res = await fetch(`${getApiBase()}/test-lab/preview?filename=${encodeURIComponent(filename)}`)
      if (res.ok) {
        const data = await res.json()
        setPreviewData(data)
      }
    } catch {
      // ignore
    } finally {
      setPreviewLoading(false)
    }
  }

  // 进度百分比
  const progress = status.meta?.current && status.meta?.total
    ? Math.round((status.meta.current / status.meta.total) * 100)
    : status.state === 'SUCCESS' ? 100 : 0

  return (
    <div className={`bg-white rounded-xl border overflow-hidden transition-all ${
      status.state === 'FAILURE' ? 'border-red-200' :
      status.state === 'SUCCESS' ? 'border-green-200' :
      'border-primary-200'
    }`}>
      {/* Header */}
      <div className={`px-5 py-3 flex items-center justify-between ${
        status.state === 'FAILURE' ? 'bg-red-50' :
        status.state === 'SUCCESS' ? 'bg-green-50' :
        'bg-primary-50'
      }`}>
        <div className="flex items-center gap-2">
          <span className="text-lg">
            {status.state === 'SUCCESS' ? '✅' :
             status.state === 'FAILURE' ? '❌' :
             status.state === 'PROGRESS' ? '🔄' : '⏳'}
          </span>
          <span className="font-medium text-sm text-slate-700">
            {taskDef?.name || triggerResult.task_id}
          </span>
          <span className="text-xs text-slate-400">
            × {triggerResult.count}
          </span>
          {triggerResult.batch_id && (
            <Link
              to={`/events?search_field=batch_id&search=${encodeURIComponent(triggerResult.batch_id)}`}
              className="text-xs font-mono text-primary-600 bg-primary-50 px-2 py-0.5 rounded hover:bg-primary-100 transition-colors"
              title="点击跳转到任务列表，查看该批次下发的所有事件"
            >
              批次: {triggerResult.batch_id} ↗
            </Link>
          )}
        </div>
        <span className="text-xs font-mono text-slate-400">
          {triggerResult.celery_task_id.slice(0, 8)}...
        </span>
      </div>

      {/* Progress Bar */}
      {isRunning && (
        <div className="px-5 py-3">
          <div className="w-full bg-slate-100 rounded-full h-2">
            <div
              className="bg-primary-500 h-2 rounded-full transition-all duration-500"
              style={{ width: `${progress}%` }}
            />
          </div>
          <div className="flex justify-between mt-2">
            <span className="text-xs text-slate-500">
              {status.meta?.step
                ? `${status.meta.step} (${status.meta.step_progress || ''})`
                : status.meta?.status || '处理中...'
              }
            </span>
            <span className="text-xs text-slate-400">
              {status.meta?.current && status.meta?.total
                ? `${status.meta.current}/${status.meta.total}`
                : ''
              }
              {status.meta?.elapsed_sec ? ` · ${status.meta.elapsed_sec}s` : ''}
            </span>
          </div>
        </div>
      )}

      {/* Result */}
      {status.state === 'SUCCESS' && status.result && (
        <div className="px-5 py-3 border-t border-green-100">
          <div className="text-sm text-slate-600 space-y-1.5">
            <div className="flex items-center gap-2">
              <span className="text-green-500">✓</span>
              <span>任务完成</span>
              {status.result.event_id && (
                <Link
                  to={`/events/${status.result.event_id}`}
                  className="text-xs text-primary-600 hover:text-primary-700 hover:underline"
                >
                  查看事件详情 ↗
                </Link>
              )}
            </div>
            {status.result.output_filename && (
              <div className="flex items-center gap-2">
                <button
                  onClick={handlePreview}
                  disabled={previewLoading}
                  className="flex items-center gap-1.5 text-xs text-primary-600 hover:text-primary-700 font-mono bg-primary-50 hover:bg-primary-100 px-2.5 py-1 rounded-lg transition-colors"
                >
                  <span>📄</span>
                  <span className="truncate max-w-[240px]">{status.result.output_filename}</span>
                  <span className="text-primary-400">{previewLoading ? '加载中...' : '👁 预览'}</span>
                </button>
              </div>
            )}
            {status.result.total_posts !== undefined && (
              <div className="text-xs text-slate-400">
                共爬取 {status.result.total_posts} 篇帖子
              </div>
            )}
            {Array.isArray(status.result.top_words) && status.result.top_words.length > 0 && (
              <div className="text-xs text-slate-400">
                🔥 热词:{' '}
                {status.result.top_words.map((tw) => {
                  const { word, count } = normalizeTopWord(tw)
                  return (
                    <span key={word} className="inline-flex items-center gap-1 bg-amber-50 text-amber-700 px-1.5 py-0.5 rounded ml-1">
                      {word}<span className="text-amber-400">×{count}</span>
                    </span>
                  )
                })}
              </div>
            )}
            {status.result.total_reports !== undefined && (
              <div className="text-xs text-slate-400">
                共生成 {status.result.total_reports} 份报告
              </div>
            )}
            {status.result.report_id && (
              <div className="text-xs text-slate-400">
                报告: <span className="font-mono">{status.result.report_id}</span>
                {status.result.data_points !== undefined && ` · ${status.result.data_points} 个数据点`}
              </div>
            )}
            {status.result.metrics && (
              <div className="flex flex-wrap gap-1.5 text-xs">
                <span className="bg-slate-100 text-slate-500 px-2 py-0.5 rounded">avg {status.result.metrics.avg_response_time_ms}ms</span>
                <span className="bg-slate-100 text-slate-500 px-2 py-0.5 rounded">p99 {status.result.metrics.p99_latency_ms}ms</span>
                <span className="bg-slate-100 text-slate-500 px-2 py-0.5 rounded">err {((status.result.metrics.error_rate ?? 0) * 100).toFixed(2)}%</span>
                <span className="bg-slate-100 text-slate-500 px-2 py-0.5 rounded">{status.result.metrics.throughput_rps} rps</span>
              </div>
            )}
            {status.result.source_url && (
              <div className="text-xs text-slate-400 font-mono truncate">
                来源: {status.result.source_url}
              </div>
            )}
          </div>
          {/* 批次事件列表 */}
          {Array.isArray(batchEvents) && batchEvents.length > 0 && (
            <div className="mt-3 pt-2 border-t border-green-100">
              <div className="text-xs text-slate-400 mb-2">批次事件 ({batchEvents.length}):</div>
              <div className="flex flex-wrap gap-1.5">
                {batchEvents.map((ev: any) => (
                  <Link
                    key={ev.id}
                    to={`/events/${ev.id}`}
                    onClick={(e) => e.stopPropagation()}
                    className={`inline-flex items-center gap-1 text-xs font-mono px-2 py-0.5 rounded transition-colors ${
                      ev.status === 'completed'
                        ? 'bg-green-100 text-green-700 hover:bg-green-200'
                        : ev.status === 'failed' || ev.status === 'dlq'
                        ? 'bg-red-100 text-red-700 hover:bg-red-200'
                        : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
                    }`}
                  >
                    {ev.status === 'completed' ? '✅' : ev.status === 'failed' ? '❌' : '⏳'}
                    {ev.id.slice(0, 8)}...
                  </Link>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {/* Error */}
      {status.state === 'FAILURE' && (
        <div className="px-5 py-3 border-t border-red-100">
          <div className="text-sm text-red-600">
            {status.meta?.error || '任务执行失败'}
          </div>
        </div>
      )}

      {/* 预览弹窗 */}
      {previewData && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40" onClick={() => setPreviewData(null)}>
          <div
            className="bg-white rounded-xl shadow-2xl w-full max-w-3xl max-h-[80vh] flex flex-col mx-4"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="flex items-center justify-between px-5 py-3 border-b border-slate-200">
              <div className="flex items-center gap-2">
                <span className="text-sm font-medium text-slate-700">📄 {previewData.filename}</span>
                <span className="text-xs text-slate-400">({(previewData.size / 1024).toFixed(1)} KB)</span>
              </div>
              <button
                onClick={() => setPreviewData(null)}
                className="text-slate-400 hover:text-slate-600 text-lg leading-none px-2 py-1 rounded hover:bg-slate-100 transition-colors"
              >
                ✕
              </button>
            </div>
            <div className="flex-1 overflow-auto p-5">
              <pre className="text-xs text-slate-600 font-mono whitespace-pre-wrap break-all bg-slate-50 rounded-lg p-4">
                {previewData.content}
              </pre>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

// ─── Constants ──────────────────────────────────

const TASK_MAP: Record<string, DemoTask> = {}

// ─── Main Page ──────────────────────────────────

export default function TestLab() {
  const [runningTasks, setRunningTasks] = useState<RunningTask[]>([])

  // 获取可用任务列表
  const { data: tasks, isLoading } = useQuery({
    queryKey: ['demo-tasks'],
    queryFn: () => apiRequest<DemoTask[]>('/test-lab/tasks'),
  })

  // 填充 TASK_MAP
  useEffect(() => {
    if (tasks) {
      tasks.forEach((t) => { TASK_MAP[t.id] = t })
    }
  }, [tasks])

  // 轮询运行中任务的状态
  useEffect(() => {
    const pendingTasks = runningTasks.filter(
      (t) => t.status.state !== 'SUCCESS' && t.status.state !== 'FAILURE'
    )
    if (pendingTasks.length === 0) return

    const interval = setInterval(async () => {
      for (const task of pendingTasks) {
        try {
          const status = await apiRequest<TaskStatus>(
            `/test-lab/status/${task.triggerResult.celery_task_id}`
          )
          setRunningTasks((prev) =>
            prev.map((t) =>
              t.triggerResult.celery_task_id === task.triggerResult.celery_task_id
                ? { ...t, status }
                : t
            )
          )
        } catch {
          // 忽略轮询错误
        }
      }
    }, 1000)

    return () => clearInterval(interval)
  }, [runningTasks])

  // 触发任务
  const handleTrigger = useCallback(async (taskId: string, count: number) => {
    try {
      const result = await apiRequest<TriggerResult>('/test-lab/trigger', {
        method: 'POST',
        body: JSON.stringify({ task_id: taskId, count }),
      })

      setRunningTasks((prev) => [
        {
          triggerResult: result,
          status: { celery_task_id: result.celery_task_id, state: 'PENDING' },
        },
        ...prev,
      ])
    } catch (err) {
      alert(`触发失败: ${err instanceof Error ? err.message : err}`)
    }
  }, [])

  const hasRunning = runningTasks.some(
    (t) => t.status.state !== 'SUCCESS' && t.status.state !== 'FAILURE'
  )

  return (
    <div className="p-6 max-w-5xl">
      {/* Header */}
      <div className="mb-6">
        <h1 className="text-2xl font-bold">🧪 测试模块</h1>
        <p className="text-sm text-slate-400 mt-1">
          人工触发真实可运行的 Demo 任务，观察事件处理全流程
        </p>
      </div>

      {/* Task Cards */}
      <div className="mb-8">
        <h2 className="text-sm font-semibold text-slate-500 uppercase tracking-wider mb-3">
          可用任务
        </h2>
        {isLoading ? (
          <div className="text-slate-400 text-sm">加载中...</div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {tasks?.map((task) => (
              <TaskCard
                key={task.id}
                task={task}
                onTrigger={handleTrigger}
                isRunning={hasRunning}
              />
            ))}
          </div>
        )}
      </div>

      {/* Running Tasks */}
      {runningTasks.length > 0 && (
        <div>
          <div className="flex items-center justify-between mb-3">
            <h2 className="text-sm font-semibold text-slate-500 uppercase tracking-wider">
              执行记录
            </h2>
            <button
              onClick={() =>
                setRunningTasks((prev) =>
                  prev.filter(
                    (t) => t.status.state === 'SUCCESS' || t.status.state === 'FAILURE'
                  )
                )
              }
              className="text-xs text-slate-400 hover:text-slate-600 transition-colors"
            >
              清除已完成
            </button>
          </div>
          <div className="space-y-3">
            {runningTasks.map((task) => (
              <RunningTaskPanel key={task.triggerResult.celery_task_id} task={task} />
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
