import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Link, useSearchParams } from 'react-router-dom'
import { eventsApi } from '../api'
import StatusBadge from '../components/StatusBadge'

const SEARCH_FIELDS = [
  { key: 'all', label: '全部字段' },
  { key: 'id', label: '事件 ID' },
  { key: 'event_type', label: '类型' },
  { key: 'resource_id', label: '资源' },
  { key: 'batch_id', label: '批次 ID' },
]

export default function EventList() {
  const [searchParams] = useSearchParams()
  const [page, setPage] = useState(1)
  const [statusFilter, setStatusFilter] = useState<string | undefined>()
  // 支持从 URL 参数初始化（如从测试模块点击批次号跳转而来）
  const [searchField, setSearchField] = useState(searchParams.get('search_field') || 'all')
  const [search, setSearch] = useState(searchParams.get('search') || '')

  const { data, isLoading } = useQuery({
    queryKey: ['events', page, statusFilter, searchField, search],
    queryFn: () => eventsApi.list({
      page,
      page_size: 15,
      status: statusFilter,
      search: search || undefined,
      search_field: searchField,
    }),
  })

  const filters = [
    { key: undefined, label: '全部' },
    { key: 'pending', label: '待处理' },
    { key: 'processing', label: '处理中' },
    { key: 'completed', label: '已完成' },
    { key: 'failed', label: '失败' },
    { key: 'dlq', label: '死信' },
  ]

  return (
    <div className="p-6">
      <div className="flex items-center justify-between mb-4">
        <h1 className="text-2xl font-bold">📋 事件列表</h1>
        <Link
          to="/events/create"
          className="px-4 py-2 bg-primary-500 text-white rounded-lg text-sm font-medium hover:bg-primary-600 transition-colors"
        >
          + 新事件
        </Link>
      </div>

      {/* Filters */}
      <div className="flex items-center gap-2 mb-4 flex-wrap">
        {filters.map((f) => (
          <button
            key={f.key ?? 'all'}
            onClick={() => { setStatusFilter(f.key); setPage(1) }}
            className={`px-3 py-1.5 rounded-lg text-sm transition-colors ${
              statusFilter === f.key
                ? 'bg-primary-50 text-primary-600 font-medium'
                : 'text-slate-500 hover:bg-slate-100'
            }`}
          >
            {f.label}
          </button>
        ))}
        <div className="ml-auto flex items-center gap-2">
          <select
            value={searchField}
            onChange={(e) => { setSearchField(e.target.value); setPage(1) }}
            className="px-2.5 py-1.5 border border-slate-200 rounded-lg text-sm bg-white focus:outline-none focus:ring-2 focus:ring-primary-200"
          >
            {SEARCH_FIELDS.map((f) => (
              <option key={f.key} value={f.key}>{f.label}</option>
            ))}
          </select>
          <input
            type="text"
            placeholder={searchField === 'batch_id' ? '输入批次 ID，如 BATCH-xxxxxxxx' : '输入搜索关键字...'}
            value={search}
            onChange={(e) => { setSearch(e.target.value); setPage(1) }}
            className="px-3 py-1.5 border border-slate-200 rounded-lg text-sm w-64 focus:outline-none focus:ring-2 focus:ring-primary-200"
          />
        </div>
      </div>

      {/* Table */}
      <div className="bg-white rounded-xl border border-slate-200 overflow-hidden">
        {isLoading ? (
          <div className="p-8 text-center text-slate-400">加载中...</div>
        ) : (
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-slate-100 bg-slate-50">
                <th className="text-left px-4 py-3 font-medium text-slate-500">事件 ID</th>
                <th className="text-left px-4 py-3 font-medium text-slate-500">类型</th>
                <th className="text-left px-4 py-3 font-medium text-slate-500">来源</th>
                <th className="text-left px-4 py-3 font-medium text-slate-500">批次号</th>
                <th className="text-left px-4 py-3 font-medium text-slate-500">状态</th>
                <th className="text-left px-4 py-3 font-medium text-slate-500">执行时间</th>
                <th className="text-left px-4 py-3 font-medium text-slate-500">接收时间</th>
                <th className="text-left px-4 py-3 font-medium text-slate-500">重试</th>
              </tr>
            </thead>
            <tbody>
              {data?.items.map((event) => (
                <tr
                  key={event.id}
                  className="border-b border-slate-50 hover:bg-slate-50 cursor-pointer"
                  onClick={() => window.location.href = `/events/${event.id}`}
                >
                  <td className="px-4 py-3 font-mono text-xs text-slate-600">
                    {event.id.slice(0, 8)}...
                  </td>
                  <td className="px-4 py-3">
                    <span className={`font-mono text-xs px-2 py-0.5 rounded ${
                      event.event_type.startsWith('demo.') ? 'bg-amber-50 text-amber-700' : 'bg-slate-100 text-slate-700'
                    }`}>
                      {event.event_type === 'demo.fetch_posts' ? '⚡ 快任务' :
                       event.event_type === 'demo.generate_report' ? '🐢 慢任务' :
                       event.event_type}
                    </span>
                  </td>
                  <td className="px-4 py-3">
                    {event.source === 'test-lab' ? (
                      <span className="text-xs bg-purple-50 text-purple-600 px-2 py-0.5 rounded font-medium">🧪 测试任务</span>
                    ) : (
                      <span className="text-slate-600">{event.source}</span>
                    )}
                  </td>
                  <td className="px-4 py-3">
                    {event.raw_payload && (event.raw_payload as any).batch_id ? (
                      <span
                        className="font-mono text-xs bg-primary-50 text-primary-600 px-2 py-0.5 rounded cursor-pointer hover:bg-primary-100"
                        onClick={(e) => {
                          e.stopPropagation()
                          setSearchField('batch_id')
                          setSearch((event.raw_payload as any).batch_id)
                          setPage(1)
                        }}
                        title="点击查看同批次事件"
                      >
                        📦 {(event.raw_payload as any).batch_id}
                      </span>
                    ) : (
                      <span className="text-xs text-slate-400">—</span>
                    )}
                  </td>
                  <td className="px-4 py-3"><StatusBadge status={event.status} /></td>
                  <td className="px-4 py-3 text-xs text-slate-500 font-mono">
                    {event.processed_at
                      ? `${((new Date(event.processed_at).getTime() - new Date(event.received_at).getTime()) / 1000).toFixed(1)}s`
                      : event.status === 'processing' ? '⏳ 进行中' : '—'}
                  </td>
                  <td className="px-4 py-3 text-slate-500 text-xs">
                    {new Date(event.received_at).toLocaleTimeString('zh-CN')}
                  </td>
                  <td className="px-4 py-3 text-xs text-slate-500">
                    {event.retry_count}/{event.max_retries}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}

        {/* Pagination */}
        {data && (
          <div className="flex items-center justify-between px-4 py-3 border-t border-slate-100 text-sm text-slate-500">
            <span>{(page - 1) * 15 + 1}-{Math.min(page * 15, data.total)} / {data.total} 条</span>
            <div className="flex gap-1">
              <button
                onClick={() => setPage(p => Math.max(1, p - 1))}
                disabled={page <= 1}
                className="px-3 py-1 border border-slate-200 rounded disabled:opacity-40 hover:bg-slate-50"
              >
                ‹
              </button>
              <span className="px-3 py-1 text-primary-600 font-medium">{page}</span>
              <button
                onClick={() => setPage(p => p + 1)}
                disabled={page * 15 >= data.total}
                className="px-3 py-1 border border-slate-200 rounded disabled:opacity-40 hover:bg-slate-50"
              >
                ›
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
