import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { eventsApi } from '../api'
import StatusBadge from '../components/StatusBadge'

export default function DlqPage() {
  const [selected, setSelected] = useState<Set<string>>(new Set())
  const queryClient = useQueryClient()

  const { data, isLoading } = useQuery({
    queryKey: ['events-dlq'],
    queryFn: () => eventsApi.list({ page_size: 50, status: 'dlq' }),
    refetchInterval: 5000,
  })

  const replayMutation = useMutation({
    mutationFn: (ids: string[]) => eventsApi.replayDlq(ids),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['events-dlq'] })
      setSelected(new Set())
    },
  })

  const toggleSelect = (id: string) => {
    setSelected(prev => {
      const next = new Set(prev)
      if (next.has(id)) next.delete(id)
      else next.add(id)
      return next
    })
  }

  const toggleAll = () => {
    if (!data) return
    if (selected.size === data.items.length) {
      setSelected(new Set())
    } else {
      setSelected(new Set(data.items.map(e => e.id)))
    }
  }

  return (
    <div className="p-6">
      <div className="flex items-center justify-between mb-4">
        <div>
          <h1 className="text-2xl font-bold">💀 死信队列</h1>
          <p className="text-sm text-slate-400 mt-1">
            重试耗尽后自动转入的事件，支持手动回放
          </p>
        </div>
        <div className="flex gap-2">
          <button
            onClick={() => setSelected(new Set())}
            disabled={selected.size === 0}
            className="px-4 py-2 border border-slate-200 rounded-lg text-sm hover:bg-slate-50 disabled:opacity-40"
          >
            取消选择 ({selected.size})
          </button>
          <button
            onClick={() => replayMutation.mutate(Array.from(selected))}
            disabled={selected.size === 0 || replayMutation.isPending}
            className="px-4 py-2 bg-primary-500 text-white rounded-lg text-sm font-medium hover:bg-primary-600 disabled:opacity-40"
          >
            {replayMutation.isPending ? '回放中...' : `↩️ 回放所选 (${selected.size})`}
          </button>
        </div>
      </div>

      {replayMutation.data && (
        <div className="mb-4 px-4 py-3 bg-green-50 text-green-700 rounded-lg text-sm">
          已回放 {replayMutation.data.replayed} 个事件
        </div>
      )}

      <div className="bg-white rounded-xl border border-slate-200 overflow-hidden">
        {isLoading ? (
          <div className="p-8 text-center text-slate-400">加载中...</div>
        ) : data && data.items.length > 0 ? (
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-slate-100 bg-slate-50">
                <th className="px-4 py-3 w-10">
                  <input
                    type="checkbox"
                    checked={data.items.length > 0 && selected.size === data.items.length}
                    onChange={toggleAll}
                    className="rounded"
                  />
                </th>
                <th className="text-left px-4 py-3 font-medium text-slate-500">事件 ID</th>
                <th className="text-left px-4 py-3 font-medium text-slate-500">类型</th>
                <th className="text-left px-4 py-3 font-medium text-slate-500">来源</th>
                <th className="text-left px-4 py-3 font-medium text-slate-500">状态</th>
                <th className="text-left px-4 py-3 font-medium text-slate-500">重试次数</th>
                <th className="text-left px-4 py-3 font-medium text-slate-500">错误信息</th>
                <th className="text-left px-4 py-3 font-medium text-slate-500">接收时间</th>
              </tr>
            </thead>
            <tbody>
              {data.items.map((event) => (
                <tr key={event.id} className="border-b border-slate-50 hover:bg-slate-50">
                  <td className="px-4 py-3">
                    <input
                      type="checkbox"
                      checked={selected.has(event.id)}
                      onChange={() => toggleSelect(event.id)}
                      className="rounded"
                    />
                  </td>
                  <td className="px-4 py-3 font-mono text-xs text-slate-600">
                    {event.id.slice(0, 8)}...
                  </td>
                  <td className="px-4 py-3">
                    <span className="font-mono text-xs bg-slate-100 px-2 py-0.5 rounded">
                      {event.event_type}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-slate-600">{event.source}</td>
                  <td className="px-4 py-3"><StatusBadge status={event.status} /></td>
                  <td className="px-4 py-3 text-xs text-slate-500">
                    {event.retry_count}/{event.max_retries}
                  </td>
                  <td className="px-4 py-3 text-xs text-red-400 max-w-xs truncate">
                    {event.error_message || '—'}
                  </td>
                  <td className="px-4 py-3 text-xs text-slate-500">
                    {new Date(event.received_at).toLocaleString('zh-CN')}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        ) : (
          <div className="p-8 text-center text-slate-400">
            🎉 没有死信事件
          </div>
        )}
      </div>
    </div>
  )
}
