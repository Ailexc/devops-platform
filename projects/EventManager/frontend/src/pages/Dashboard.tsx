import { useQuery } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import { statsApi } from '../api'
import StatusBadge from '../components/StatusBadge'

function WorkerPanel() {
  const { data: workers } = useQuery({
    queryKey: ['workers'],
    queryFn: statsApi.workers,
    refetchInterval: 10000,
  })
  const { data: queues } = useQuery({
    queryKey: ['queues'],
    queryFn: statsApi.queues,
    refetchInterval: 10000,
  })

  return (
    <div className="bg-white rounded-xl border border-slate-200 p-5">
      <h2 className="text-sm font-semibold text-slate-700 mb-3">⚙️ Worker & 队列</h2>

      {/* Worker status */}
      <div className="flex items-center gap-2 mb-3 pb-3 border-b border-slate-100">
        <span className={`w-2 h-2 rounded-full ${workers && workers.online > 0 ? 'bg-green-400' : 'bg-red-400'}`} />
        <span className="text-sm text-slate-600">
          Celery Worker: <strong>{workers?.online ?? '—'}/{workers?.total ?? '—'}</strong> 在线
        </span>
        <span className="text-xs text-slate-400 ml-auto">
          🔄 {workers?.active_tasks ?? 0} 活跃 / ⏳ {workers?.queued_tasks ?? 0} 排队
        </span>
      </div>

      {/* Queue depth bars */}
      <div className="space-y-2">
        {queues?.filter(q => q.depth > 0).slice(0, 4).map((q) => {
          const maxDepth = Math.max(...queues.map(x => x.depth), 1)
          const pct = (q.depth / maxDepth) * 100
          const barColor =
            q.name === 'events.dlq' ? 'bg-purple-500' :
            q.name === 'events.retry' ? 'bg-amber-500' :
            q.name === 'events.high' ? 'bg-blue-500' :
            'bg-primary-500'
          return (
            <div key={q.name}>
              <div className="flex justify-between text-xs mb-0.5">
                <span className="text-slate-500">{q.label}</span>
                <span className="font-mono text-slate-600">{q.depth}</span>
              </div>
              <div className="h-2 bg-slate-100 rounded-full overflow-hidden">
                <div className={`h-full rounded-full transition-all duration-500 ${barColor}`} style={{ width: `${pct}%` }} />
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}

function RecentFailures() {
  const { data: failures } = useQuery({
    queryKey: ['recent-failures'],
    queryFn: () => statsApi.recentFailures(6),
    refetchInterval: 10000,
  })

  return (
    <div className="bg-white rounded-xl border border-slate-200 p-5">
      <div className="flex items-center justify-between mb-3">
        <h2 className="text-sm font-semibold text-slate-700">❌ 最近失败事件</h2>
        <Link to="/events?status=failed" className="text-xs text-primary-500 hover:underline">查看全部 →</Link>
      </div>
      {failures && failures.length > 0 ? (
        <div className="space-y-2">
          {failures.map((f) => (
            <Link
              key={f.id}
              to={`/events/${f.id}`}
              className="flex items-center gap-2 text-sm bg-slate-50 rounded-lg px-3 py-2 hover:bg-red-50 transition-colors group"
            >
              <span className="text-red-400">❌</span>
              <span className="font-mono text-xs text-slate-600 bg-white px-1.5 py-0.5 rounded flex-shrink-0">
                {f.event_type}
              </span>
              <span className="flex-1 text-slate-500 truncate text-xs">{f.error_message || 'Unknown error'}</span>
              <span className="text-xs text-slate-400">
                {f.retry_count}/{f.max_retries}
              </span>
              <span className="text-xs text-slate-300 group-hover:text-primary-500">→</span>
            </Link>
          ))}
        </div>
      ) : (
        <div className="text-sm text-slate-400 text-center py-4">🎉 暂无失败事件</div>
      )}
    </div>
  )
}

function ThroughputChart() {
  const { data: throughput } = useQuery({
    queryKey: ['throughput'],
    queryFn: statsApi.throughput,
    refetchInterval: 30000,
  })

  const maxVal = throughput ? Math.max(...throughput.map(h => h.total), 1) : 1

  return (
    <div className="bg-white rounded-xl border border-slate-200 p-5">
      <h2 className="text-sm font-semibold text-slate-700 mb-3">📈 事件吞吐量趋势（24h）</h2>
      {throughput && throughput.length > 0 ? (
        <div className="flex items-end gap-1 h-32">
          {throughput.slice(-24).map((h) => {
            const totalPct = (h.total / maxVal) * 100
            const failedPct = (h.failed / maxVal) * 100
            const completedPct = (h.completed / maxVal) * 100
            return (
              <div key={h.hour} className="flex-1 flex flex-col items-center justify-end h-full relative group">
                {/* Stacked bar */}
                <div className="w-full max-w-[24px] flex flex-col-reverse items-center h-full">
                  {h.failed > 0 && (
                    <div
                      className="w-full bg-red-400 rounded-t"
                      style={{ height: `${Math.max(failedPct, 0.5)}%` }}
                      title={`${h.hour}: ${h.failed} failed`}
                    />
                  )}
                  {h.completed > 0 && (
                    <div
                      className="w-full bg-green-400"
                      style={{ height: `${Math.max(completedPct, 0.5)}%` }}
                      title={`${h.hour}: ${h.completed} completed`}
                    />
                  )}
                </div>
                {/* Tooltip on hover */}
                <div className="absolute bottom-full mb-1 hidden group-hover:block bg-slate-800 text-white text-xs rounded px-2 py-1 whitespace-nowrap z-10">
                  {h.hour.split(' ')[1]} | ✅ {h.completed} ❌ {h.failed}
                </div>
              </div>
            )
          })}
        </div>
      ) : (
        <div className="text-sm text-slate-400 text-center py-8">暂无数据</div>
      )}
      <div className="flex justify-center gap-4 mt-2 text-xs text-slate-400">
        <span className="flex items-center gap-1"><span className="w-2 h-2 rounded bg-green-400" /> 成功</span>
        <span className="flex items-center gap-1"><span className="w-2 h-2 rounded bg-red-400" /> 失败</span>
      </div>
    </div>
  )
}

export default function Dashboard() {
  const { data: stats, isLoading } = useQuery({
    queryKey: ['stats'],
    queryFn: statsApi.get,
    refetchInterval: 5000,
  })

  if (isLoading) {
    return (
      <div className="p-6">
        <h1 className="text-2xl font-bold mb-6">📊 实时监控仪表盘</h1>
        <div className="text-slate-400">加载中...</div>
      </div>
    )
  }

  const statusLabels: Record<string, string> = {
    pending: '待处理', processing: '处理中', completed: '已完成',
    failed: '失败', dlq: '死信',
  }

  return (
    <div className="p-6">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold">📊 实时监控仪表盘</h1>
        <span className="text-xs text-slate-400 flex items-center gap-1">
          <span className="w-2 h-2 rounded-full bg-green-400 animate-pulse" />
          实时更新 (5s)
        </span>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-4 gap-4 mb-6">
        <div className="bg-white rounded-xl border border-slate-200 p-5 text-center">
          <div className="text-3xl font-bold text-primary-500">{stats?.total ?? 0}</div>
          <div className="text-sm text-slate-500 mt-1">今日事件总数</div>
        </div>
        <div className="bg-white rounded-xl border border-slate-200 p-5 text-center">
          <div className="text-3xl font-bold text-amber-500">{stats?.by_status?.processing ?? 0}</div>
          <div className="text-sm text-slate-500 mt-1">处理中</div>
        </div>
        <div className="bg-white rounded-xl border border-slate-200 p-5 text-center">
          <div className="text-3xl font-bold text-red-500">{stats?.by_status?.failed ?? 0}</div>
          <div className="text-sm text-slate-500 mt-1">失败</div>
          <div className="text-xs text-slate-400 mt-0.5">成功率 {stats?.success_rate ?? 0}%</div>
        </div>
        <div className="bg-white rounded-xl border border-slate-200 p-5 text-center">
          <div className="text-3xl font-bold text-green-500">{stats?.by_status?.completed ?? 0}</div>
          <div className="text-sm text-slate-500 mt-1">已完成</div>
          <div className="text-xs text-slate-400 mt-0.5">队列深度 {stats?.queue_depth ?? 0}</div>
        </div>
      </div>

      {/* Mid section: status + worker */}
      <div className="grid grid-cols-3 gap-4 mb-6">
        {/* Status distribution */}
        <div className="bg-white rounded-xl border border-slate-200 p-5">
          <h2 className="text-sm font-semibold text-slate-700 mb-3">状态分布</h2>
          <div className="space-y-2">
            {stats?.by_status && Object.entries(stats.by_status).map(([status, count]) => (
              <div key={status} className="flex items-center justify-between text-sm">
                <span className="text-slate-600">{statusLabels[status] ?? status}</span>
                <div className="flex items-center gap-2 flex-1 ml-2">
                  <div className="flex-1 h-2 bg-slate-100 rounded-full overflow-hidden">
                    <div
                      className="h-full bg-primary-500 rounded-full"
                      style={{ width: `${stats.total > 0 ? (count / stats.total) * 100 : 0}%` }}
                    />
                  </div>
                  <span className="text-slate-500 w-8 text-right text-xs font-mono">{count}</span>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Worker & Queue */}
        <WorkerPanel />

        {/* Latency & Activity */}
        <div className="bg-white rounded-xl border border-slate-200 p-5">
          <h2 className="text-sm font-semibold text-slate-700 mb-3">⏱️ 延迟 & 活动</h2>
          <div className="space-y-3">
            <div className="flex justify-between text-sm">
              <span className="text-slate-600">平均耗时</span>
              <span className="font-mono text-slate-800">
                {stats?.avg_duration != null ? `${stats.avg_duration}s` : '—'}
              </span>
            </div>
            <div className="flex justify-between text-sm">
              <span className="text-slate-600">P99 延迟</span>
              <span className="font-mono text-slate-800">
                {stats?.p99_duration != null ? `${stats.p99_duration}s` : '—'}
              </span>
            </div>
            <div className="flex justify-between text-sm">
              <span className="text-slate-600">活跃任务</span>
              <span className="font-mono text-slate-800">{stats?.by_status?.processing ?? 0}</span>
            </div>
            <div className="flex justify-between text-sm">
              <span className="text-slate-600">队列积压</span>
              <span className="font-mono text-slate-800">{stats?.queue_depth ?? 0}</span>
            </div>
            <div className="pt-2 border-t border-slate-100">
              <div className="flex justify-between text-sm">
                <span className="text-slate-600">成功率 (最近1h)</span>
                <span className={`font-mono ${(stats?.success_rate ?? 100) >= 95 ? 'text-green-600' : 'text-red-600'}`}>
                  {stats?.success_rate ?? 0}%
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Bottom row: throughput + recent failures */}
      <div className="grid grid-cols-2 gap-4">
        <ThroughputChart />
        <RecentFailures />
      </div>
    </div>
  )
}
