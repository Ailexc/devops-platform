import { useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { eventsApi, getApiBase, normalizeTopWord } from '../api'
import StatusBadge from '../components/StatusBadge'

export default function EventDetail() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const queryClient = useQueryClient()

  const { data: event, isLoading } = useQuery({
    queryKey: ['event', id],
    queryFn: () => eventsApi.get(id!),
    enabled: !!id,
    refetchInterval: 3000,
  })

  const { data: logs } = useQuery({
    queryKey: ['event-logs', id],
    queryFn: () => eventsApi.getLogs(id!),
    enabled: !!id,
    refetchInterval: 3000,
  })

  const retryMutation = useMutation({
    mutationFn: () => eventsApi.retry(id!),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['event', id] })
      queryClient.invalidateQueries({ queryKey: ['event-logs', id] })
    },
  })

  if (isLoading) {
    return <div className="p-6 text-slate-400">加载中...</div>
  }
  if (!event) {
    return <div className="p-6 text-red-500">事件不存在</div>
  }

  const actionLabels: Record<string, { icon: string; label: string; color: string }> = {
    received:    { icon: '📥', label: '接收事件',  color: 'bg-blue-400' },
    enqueued:    { icon: '📮', label: '投递队列',  color: 'bg-indigo-400' },
    routed:      { icon: '🔀', label: '路由匹配',  color: 'bg-purple-400' },
    processing:  { icon: '⚡', label: 'Worker 消费', color: 'bg-amber-400 animate-pulse' },
    retrying:    { icon: '🔄', label: '自动重试',  color: 'bg-orange-400 animate-pulse' },
    completed:   { icon: '✅', label: '处理完成',  color: 'bg-green-400' },
    failed:      { icon: '❌', label: '处理失败',  color: 'bg-red-400' },
    dlq:         { icon: '💀', label: '转入死信',  color: 'bg-red-600' },
    retry_manual:{ icon: '🔁', label: '手动重试',  color: 'bg-cyan-400' },
    replayed:    { icon: '↩️', label: '已回放',    color: 'bg-teal-400' },
  }

  return (
    <div className="p-6 max-w-4xl">
      <button
        onClick={() => navigate('/events')}
        className="text-sm text-slate-400 hover:text-slate-600 mb-4"
      >
        ← 返回事件列表
      </button>

      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold">📄 事件详情</h1>
          <p className="text-xs font-mono text-slate-400 mt-1">{event.id}</p>
        </div>
        <div className="flex gap-2">
          <button
            onClick={() => retryMutation.mutate()}
            disabled={retryMutation.isPending || event.status === 'processing'}
            className="px-4 py-2 border border-slate-200 rounded-lg text-sm hover:bg-slate-50 disabled:opacity-40"
          >
            🔁 重试
          </button>
          <button
            onClick={() => navigator.clipboard.writeText(JSON.stringify(event, null, 2))}
            className="px-4 py-2 border border-slate-200 rounded-lg text-sm hover:bg-slate-50"
          >
            📋 复制
          </button>
        </div>
      </div>

      <div className="grid grid-cols-2 gap-4 mb-6">
        {/* Info Panel */}
        <div className="bg-white rounded-xl border border-slate-200 p-5">
          <div className="space-y-3">
            <div className="flex"><span className="w-28 text-slate-400 text-sm">事件类型</span><span className="text-sm font-mono">{event.event_type}</span></div>
            <div className="flex"><span className="w-28 text-slate-400 text-sm">来源</span><span className="text-sm">{event.source}</span></div>
            <div className="flex"><span className="w-28 text-slate-400 text-sm">资源 ID</span><span className="text-sm font-mono">{event.resource_id || '—'}</span></div>
            {event.raw_payload && (event.raw_payload as any).batch_id && (
              <div className="flex">
                <span className="w-28 text-slate-400 text-sm">批次号</span>
                <a
                  href={`/events?search=${(event.raw_payload as any).batch_id}`}
                  className="text-sm font-mono text-primary-600 hover:text-primary-700 hover:underline"
                >
                  📦 {(event.raw_payload as any).batch_id}
                </a>
              </div>
            )}
            <div className="flex"><span className="w-28 text-slate-400 text-sm">状态</span><StatusBadge status={event.status} /></div>
            <div className="flex"><span className="w-28 text-slate-400 text-sm">接收时间</span><span className="text-sm">{new Date(event.received_at).toLocaleString('zh-CN')}</span></div>
            <div className="flex"><span className="w-28 text-slate-400 text-sm">处理节点</span><span className="text-sm font-mono">{event.worker_id || '—'}</span></div>
            <div className="flex"><span className="w-28 text-slate-400 text-sm">重试次数</span><span className="text-sm">{event.retry_count}/{event.max_retries}</span></div>
            {event.error_message && (
              <div className="flex"><span className="w-28 text-slate-400 text-sm">错误信息</span><span className="text-sm text-red-500">{event.error_message}</span></div>
            )}
          </div>
        </div>

        {/* Timeline */}
        <div className="bg-white rounded-xl border border-slate-200 p-5">
          <h2 className="text-sm font-semibold text-slate-700 mb-3">⏱️ 处理时间线</h2>
          {logs && logs.length > 0 ? (
            <div className="space-y-0">
              {logs.map((log, i) => {
                const meta = actionLabels[log.action] ?? { icon: '●', label: log.action, color: 'bg-slate-300' }
                const detail = log.detail || {}
                const isError = log.action === 'failed' || log.action === 'dlq'
                const isSuccess = log.action === 'completed'
                const isAnimated = log.action === 'processing' || log.action === 'retrying'
                return (
                  <div key={log.id} className="flex gap-3 pb-4 relative">
                    {i < logs.length - 1 && (
                      <div className="absolute left-[7px] top-5 bottom-0 w-px bg-slate-200" />
                    )}
                    {/* 节点圆点 */}
                    <div className={`w-3.5 h-3.5 rounded-full mt-1 flex-shrink-0 border-2 border-white ${meta.color} ${isAnimated ? '' : ''}`} />
                    {/* 内容 */}
                    <div className="flex-1 min-w-0">
                      {/* 标题行 */}
                      <div className="flex items-center gap-2">
                        <span className="text-sm font-medium text-slate-700">{meta.icon} {meta.label}</span>
                        <span className="text-xs text-slate-400 font-mono">
                          {new Date(log.created_at).toLocaleTimeString('zh-CN')}
                        </span>
                      </div>
                      {/* 结构化详情 */}
                      <div className="mt-1 flex flex-wrap gap-1.5">
                        {log.action === 'received' && (
                          <>
                            <DetailTag label="来源" value={detail.source} />
                            <DetailTag label="类型" value={detail.event_type} />
                          </>
                        )}
                        {log.action === 'enqueued' && (
                          <>
                            <DetailTag label="队列" value={detail.queue} color="indigo" />
                            <DetailTag label="Task ID" value={String(detail.celery_task_id || '').slice(0, 8)} mono />
                            {detail.trigger && <DetailTag label="触发" value={String(detail.trigger)} />}
                          </>
                        )}
                        {log.action === 'routed' && (
                          <>
                            <DetailTag label="Handler" value={detail.handler} color="purple" />
                            <DetailTag label="匹配" value={detail.event_type} />
                          </>
                        )}
                        {log.action === 'processing' && (
                          <>
                            <DetailTag label="Worker" value={detail.worker} color="amber" />
                            {detail.pid && <DetailTag label="PID" value={String(detail.pid)} mono />}
                            {detail.queue && <DetailTag label="队列" value={String(detail.queue)} />}
                          </>
                        )}
                        {log.action === 'completed' && (
                          <>
                            <DetailTag label="Handler" value={detail.handler} color="green" />
                            {detail.result && <DetailTag label="结果" value={String(detail.result)} />}
                            {detail.duration_ms !== undefined && (
                              <DetailTag label="耗时" value={`${detail.duration_ms}ms`} color="green" />
                            )}
                          </>
                        )}
                        {log.action === 'failed' && (
                          <>
                            <DetailTag label="错误" value={String(detail.error || '')} color="red" />
                            {detail.retry_count !== undefined && (
                              <DetailTag label="重试" value={`${detail.retry_count}/${detail.max_retries}`} color="red" />
                            )}
                          </>
                        )}
                        {log.action === 'retrying' && (
                          <>
                            <DetailTag label="下次重试" value={`${detail.countdown_s}s 后`} color="orange" />
                            <DetailTag label="第几次" value={`${detail.retry_count}/${detail.max_retries}`} />
                          </>
                        )}
                        {log.action === 'dlq' && (
                          <>
                            <DetailTag label="原因" value={String(detail.reason || '')} color="red" />
                            {detail.error && <DetailTag label="错误" value={String(detail.error)} color="red" />}
                            {detail.total_retries && <DetailTag label="总重试" value={String(detail.total_retries)} />}
                          </>
                        )}
                        {log.action === 'retry_manual' && (
                          <>
                            <DetailTag label="触发者" value={String(detail.triggered_by || '')} color="cyan" />
                            {detail.previous_status && <DetailTag label="之前状态" value={String(detail.previous_status)} />}
                          </>
                        )}
                      </div>
                      {/* 未识别的 action 也显示 detail */}
                      {!actionLabels[log.action] && (
                        <div className="mt-1 text-xs text-slate-400 font-mono">
                          {JSON.stringify(detail)}
                        </div>
                      )}
                    </div>
                  </div>
                )
              })}
            </div>
          ) : (
            <div className="text-sm text-slate-400">暂无日志</div>
          )}
        </div>
      </div>

      {/* Raw Payload */}
      <div className="bg-white rounded-xl border border-slate-200 p-5 mb-6">
        <h2 className="text-sm font-semibold text-slate-700 mb-3">📦 原始 Payload</h2>
        <pre className="bg-slate-50 rounded-lg p-4 text-xs font-mono overflow-x-auto max-h-64">
          {JSON.stringify(event.raw_payload, null, 2)}
        </pre>
      </div>

      {/* 执行产物预览 — 仅 demo 事件显示 */}
      {event.source === 'test-lab' && (
        <ArtifactPreview eventType={event.event_type} rawPayload={event.raw_payload} />
      )}
    </div>
  )
}

// ─── 时间线详情标签 ──────────────────────────────────

function DetailTag({ label, value, color, mono }: {
  label: string; value: unknown; color?: string; mono?: boolean
}) {
  if (value === undefined || value === null || value === '') return null
  const strVal = String(value)
  const colorMap: Record<string, string> = {
    indigo: 'bg-indigo-50 text-indigo-600',
    purple: 'bg-purple-50 text-purple-600',
    amber:  'bg-amber-50 text-amber-600',
    green:  'bg-green-50 text-green-600',
    red:    'bg-red-50 text-red-600',
    orange: 'bg-orange-50 text-orange-600',
    cyan:   'bg-cyan-50 text-cyan-600',
  }
  const cls = color ? (colorMap[color] || 'bg-slate-100 text-slate-600') : 'bg-slate-100 text-slate-500'
  return (
    <span className={`inline-flex items-center gap-1 text-xs px-2 py-0.5 rounded-full ${cls}`}>
      <span className="opacity-60">{label}</span>
      <span className={mono ? 'font-mono' : 'font-medium'}>{strVal}</span>
    </span>
  )
}

// ─── 执行产物预览组件 ──────────────────────────────────

function ArtifactPreview({ eventType, rawPayload }: { eventType: string; rawPayload: Record<string, unknown> }) {
  const [content, setContent] = useState<string | null>(null)
  const [filename, setFilename] = useState('')
  const [size, setSize] = useState(0)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const outputFilename = rawPayload?.output_filename as string | undefined
  const isFetch = eventType === 'demo.fetch_posts'
  const result = rawPayload?.result as Record<string, unknown> | undefined
  const report = rawPayload?.report as Record<string, unknown> | undefined

  const handleLoad = async () => {
    if (!outputFilename) return
    setLoading(true)
    setError('')
    try {
      const res = await fetch(`${getApiBase()}/test-lab/preview?filename=${encodeURIComponent(outputFilename)}`)
      if (!res.ok) {
        setError(`预览失败: ${res.status} ${res.statusText}`)
        return
      }
      const data = await res.json()
      setContent(data.content)
      setFilename(data.filename)
      setSize(data.size)
    } catch {
      setError('预览请求失败')
    } finally {
      setLoading(false)
    }
  }

  const taskLabel = isFetch ? '📡 API 数据爬取' : '📊 报告生成'

  return (
    <div className="bg-white rounded-xl border border-slate-200 overflow-hidden">
      <div className="px-5 py-3 bg-slate-50 border-b border-slate-200 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <span className="text-sm font-semibold text-slate-700">📁 任务结果与执行产物</span>
          <span className="text-xs bg-primary-50 text-primary-600 px-2 py-0.5 rounded-full">{taskLabel}</span>
        </div>
        {outputFilename && !content && (
          <button
            onClick={handleLoad}
            disabled={loading}
            className="px-3 py-1.5 bg-primary-500 text-white rounded-lg text-xs font-medium hover:bg-primary-600 disabled:opacity-40 transition-colors"
          >
            {loading ? '加载中...' : '👁 预览产物'}
          </button>
        )}
      </div>

      {/* 任务结果摘要 */}
      {(isFetch && result) || (!isFetch && report) ? (
        <div className="px-5 py-3 border-b border-slate-100 space-y-1.5">
          {isFetch && result && (
            <>
              <div className="text-xs text-slate-500">
                ✅ 状态: <span className="font-medium text-green-600">{result.success ? '成功' : '失败'}</span>
              </div>
              {result.batch !== undefined && (
                <div className="text-xs text-slate-500">批次: <span className="font-mono">{String(result.batch)}</span></div>
              )}
              {result.total_posts !== undefined && (
                <div className="text-xs text-slate-500">共爬取 <span className="font-medium">{String(result.total_posts)}</span> 篇帖子</div>
              )}
              {Array.isArray(result.top_words) && result.top_words.length > 0 && (
                <div className="flex flex-wrap gap-1.5 text-xs items-center">
                  <span className="text-slate-500">🔥 热词:</span>
                  {result.top_words.map((tw) => {
                    const { word, count } = normalizeTopWord(tw)
                    return (
                      <span key={word} className="inline-flex items-center gap-1 bg-amber-50 text-amber-700 px-1.5 py-0.5 rounded">
                        {word}<span className="text-amber-400">×{count}</span>
                      </span>
                    )
                  })}
                </div>
              )}
              {result.source_url && (
                <div className="text-xs text-slate-400 font-mono truncate">来源: {String(result.source_url)}</div>
              )}
              {result.error && (
                <div className="text-xs text-red-500">错误: {String(result.error)}</div>
              )}
            </>
          )}
          {!isFetch && report && (
            <>
              <div className="text-xs text-slate-500">报告: <span className="font-mono">{String(report.report_id)}</span></div>
              {report.data_points !== undefined && (
                <div className="text-xs text-slate-500">{String(report.data_points)} 个数据点</div>
              )}
              {report.metrics && (
                <div className="flex flex-wrap gap-1.5 text-xs">
                  <span className="bg-slate-100 text-slate-500 px-2 py-0.5 rounded">avg {(report.metrics as any).avg_response_time_ms}ms</span>
                  <span className="bg-slate-100 text-slate-500 px-2 py-0.5 rounded">p99 {(report.metrics as any).p99_latency_ms}ms</span>
                  <span className="bg-slate-100 text-slate-500 px-2 py-0.5 rounded">err {((report.metrics as any).error_rate * 100).toFixed(2)}%</span>
                  <span className="bg-slate-100 text-slate-500 px-2 py-0.5 rounded">{(report.metrics as any).throughput_rps} rps</span>
                </div>
              )}
              {report.summary && (
                <div className="text-xs text-slate-400">{String(report.summary)}</div>
              )}
            </>
          )}
        </div>
      ) : null}

      {/* 文件信息 */}
      {outputFilename && (
        <div className="px-5 py-3 border-b border-slate-100">
          <div className="flex items-center gap-3 text-xs text-slate-500">
            <span className="font-mono">📄 {outputFilename}</span>
            {size > 0 && <span className="text-slate-400">({(size / 1024).toFixed(1)} KB)</span>}
          </div>
        </div>
      )}

      {/* 错误 */}
      {error && (
        <div className="px-5 py-3">
          <div className="text-sm text-red-500 bg-red-50 rounded-lg px-4 py-2">{error}</div>
        </div>
      )}

      {/* 内容预览 */}
      {content && (
        <div className="p-5">
          <pre className="bg-slate-50 rounded-lg p-4 text-xs font-mono overflow-x-auto max-h-96 whitespace-pre-wrap break-all text-slate-600">
            {content}
          </pre>
        </div>
      )}
    </div>
  )
}
