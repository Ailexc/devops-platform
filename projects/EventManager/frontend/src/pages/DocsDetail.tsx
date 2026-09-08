import { useParams, useNavigate } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { docsApi, getApiBase } from '../api'

export default function DocsDetail() {
  const { filename } = useParams<{ filename: string }>()
  const navigate = useNavigate()

  const { data: docs } = useQuery({
    queryKey: ['docs'],
    queryFn: () => docsApi.list(),
  })

  const doc = docs?.find((d) => d.filename === filename)

  return (
    <div className="p-6">
      <div className="flex items-center justify-between mb-4">
        <button
          onClick={() => navigate('/docs')}
          className="text-sm text-slate-400 hover:text-slate-600"
        >
          ← 返回文档列表
        </button>
        {doc && (
          <div className="flex items-center gap-3 text-xs text-slate-400">
            <span className="font-mono">{doc.filename}</span>
            <span>{doc.modified_at}</span>
          </div>
        )}
      </div>

      <h1 className="text-xl font-bold mb-4">📄 {doc?.title || filename}</h1>

      <div className="bg-white rounded-xl border border-slate-200 overflow-hidden">
        {filename ? (
          <iframe
            src={`${getApiBase()}/docs/${encodeURIComponent(filename)}`}
            title={doc?.title || filename}
            className="w-full"
            style={{ height: 'calc(100vh - 220px)', minHeight: 600 }}
          />
        ) : (
          <div className="p-8 text-center text-slate-400 text-sm">文档不存在</div>
        )}
      </div>
    </div>
  )
}
