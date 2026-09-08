import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { handlersApi } from '../api'

interface EventType {
  category: string
  icon: string
  pattern: string
  handler: string
  description: string
  events?: { type: string; desc: string }[]
  schema?: Record<string, { type: string; required: boolean; desc: string; default?: any; example?: any }>
  example?: Record<string, any>
}

function SchemaTable({ schema }: { schema: EventType['schema'] }) {
  if (!schema || Object.keys(schema).length === 0) return null
  return (
    <div className="overflow-x-auto">
      <table className="w-full text-xs">
        <thead>
          <tr className="border-b border-slate-200 bg-slate-50">
            <th className="text-left px-3 py-2 font-medium text-slate-500 w-36">字段</th>
            <th className="text-left px-3 py-2 font-medium text-slate-500 w-20">类型</th>
            <th className="text-center px-3 py-2 font-medium text-slate-500 w-14">必填</th>
            <th className="text-left px-3 py-2 font-medium text-slate-500">说明</th>
            <th className="text-left px-3 py-2 font-medium text-slate-500">示例值</th>
          </tr>
        </thead>
        <tbody>
          {Object.entries(schema).map(([field, info]) => (
            <tr key={field} className="border-b border-slate-100 hover:bg-slate-50">
              <td className="px-3 py-2 font-mono text-slate-700">{field}</td>
              <td className="px-3 py-2 text-slate-500">{info.type}</td>
              <td className="px-3 py-2 text-center">
                {info.required ? <span className="text-red-400 font-bold">是</span> : <span className="text-slate-300">否</span>}
              </td>
              <td className="px-3 py-2 text-slate-600">
                {info.desc}
                {info.default !== undefined && <span className="text-slate-400 ml-1">(默认: {JSON.stringify(info.default)})</span>}
              </td>
              <td className="px-3 py-2 font-mono text-xs text-slate-500">{info.example !== undefined ? JSON.stringify(info.example) : '—'}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

function EventRow({ ev, schema, example }: { ev: { type: string; desc: string }; schema?: EventType['schema']; example?: Record<string, any> }) {
  const [open, setOpen] = useState(false)
  const hasDetail = (schema && Object.keys(schema).length > 0) || example

  return (
    <div className="border border-slate-100 rounded-lg overflow-hidden bg-white">
      <button
        onClick={() => setOpen(!open)}
        className="w-full flex items-center gap-3 px-4 py-3 text-left hover:bg-slate-50 transition-colors"
      >
        <span className={`text-xs font-mono bg-primary-50 text-primary-600 px-2 py-1 rounded font-medium`}>
          {ev.type}
        </span>
        <span className="text-sm text-slate-600 flex-1">{ev.desc}</span>
        {hasDetail && (
          <span className={`text-xs text-slate-300 transition-transform ${open ? 'rotate-180' : ''}`}>▼</span>
        )}
      </button>
      {open && hasDetail && (
        <div className="border-t border-slate-100 px-4 py-3 space-y-4 bg-slate-50/50">
          {schema && Object.keys(schema).length > 0 && (
            <div>
              <h5 className="text-xs font-semibold text-slate-500 uppercase tracking-wider mb-2">📥 请求参数</h5>
              <SchemaTable schema={schema} />
            </div>
          )}
          {example && (
            <div>
              <h5 className="text-xs font-semibold text-slate-500 uppercase tracking-wider mb-2">📦 请求示例</h5>
              <pre className="bg-slate-800 text-slate-100 rounded-lg p-3 text-xs font-mono overflow-x-auto">
                {JSON.stringify(example, null, 2)}
              </pre>
            </div>
          )}
        </div>
      )}
    </div>
  )
}

function HandlerSection({ t }: { t: EventType }) {
  const [collapsed, setCollapsed] = useState(false)

  return (
    <div className="bg-white rounded-xl border border-slate-200 overflow-hidden">
      {/* Section header */}
      <button
        onClick={() => setCollapsed(!collapsed)}
        className="w-full flex items-center gap-3 px-5 py-4 text-left hover:bg-slate-50 transition-colors border-b border-slate-100"
      >
        <span className="text-2xl">{t.icon}</span>
        <div className="flex-1">
          <div className="flex items-center gap-2">
            <h2 className="text-base font-bold text-slate-800">{t.category}</h2>
            <span className="text-xs bg-slate-100 text-slate-500 px-2 py-0.5 rounded font-mono">
              {t.handler}
            </span>
            <span className="text-xs text-slate-400 font-mono ml-1">{t.pattern}</span>
          </div>
          <p className="text-sm text-slate-500 mt-0.5">{t.description}</p>
        </div>
        <span className={`text-sm text-slate-300 transition-transform ${collapsed ? '' : 'rotate-180'}`}>▼</span>
      </button>

      {/* Event list */}
      {!collapsed && t.events && (
        <div className="px-4 py-3 space-y-2">
          {t.events.map((ev) => (
            <EventRow key={ev.type} ev={ev} schema={t.schema} example={t.example} />
          ))}
        </div>
      )}
    </div>
  )
}

export default function EventTypes() {
  const { data: types, isLoading } = useQuery({
    queryKey: ['event-types'],
    queryFn: handlersApi.listTypes,
  })

  return (
    <div className="p-6 max-w-4xl">
      <h1 className="text-2xl font-bold mb-2">📋 支持的事件类型</h1>
      <p className="text-sm text-slate-400 mb-6">
        系统当前支持以下事件类型，展开可查看每个事件的参数结构和请求示例。
      </p>

      {isLoading ? (
        <div className="text-slate-400">加载中...</div>
      ) : (
        <div className="space-y-4">
          {types?.map((t: EventType) => (
            <HandlerSection key={t.pattern} t={t} />
          ))}
        </div>
      )}

      <div className="mt-6 bg-amber-50 border border-amber-200 rounded-xl p-4 text-sm text-amber-800">
        <strong>💡 未匹配的事件</strong>
        <p className="mt-1">
          任何不匹配上述模式的事件会被 <code className="bg-amber-100 px-1 rounded">EchoHandler</code> 兜底处理。
        </p>
      </div>
    </div>
  )
}
