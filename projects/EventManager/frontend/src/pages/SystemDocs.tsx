import { useQuery } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import { docsApi, DocInfo } from '../api'

function formatSize(bytes: number) {
  if (bytes >= 1024 * 1024) return `${(bytes / 1024 / 1024).toFixed(1)} MB`
  if (bytes >= 1024) return `${(bytes / 1024).toFixed(1)} KB`
  return `${bytes} B`
}

function DocCard({ doc }: { doc: DocInfo }) {
  return (
    <Link
      to={`/docs/${encodeURIComponent(doc.filename)}`}
      className="bg-white rounded-xl border border-slate-200 p-5 hover:shadow-md hover:border-primary-200 transition-all flex flex-col group"
    >
      <div className="text-3xl mb-3 group-hover:scale-110 transition-transform">📄</div>
      <h3 className="text-base font-semibold text-slate-800 mb-1 group-hover:text-primary-600 transition-colors">
        {doc.title}
      </h3>
      <p className="text-sm text-slate-500 flex-1 mb-3 line-clamp-3">
        {doc.description || '暂无描述'}
      </p>
      <div className="flex items-center gap-2 text-xs text-slate-400 border-t border-slate-100 pt-3">
        <span className="font-mono truncate">{doc.filename}</span>
        <span className="ml-auto flex-shrink-0">{formatSize(doc.size)}</span>
        <span className="flex-shrink-0">🕐 {doc.modified_at}</span>
      </div>
    </Link>
  )
}

export default function SystemDocs() {
  const { data: docs, isLoading } = useQuery({
    queryKey: ['docs'],
    queryFn: () => docsApi.list(),
  })

  return (
    <div className="p-6">
      <div className="mb-6">
        <h1 className="text-2xl font-bold">📚 系统文档</h1>
        <p className="text-sm text-slate-400 mt-1">
          项目架构设计与技术文档（docs 目录下所有 HTML 文档）
        </p>
      </div>

      {isLoading ? (
        <div className="text-slate-400 text-sm">加载中...</div>
      ) : docs && docs.length > 0 ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {docs.map((doc) => (
            <DocCard key={doc.filename} doc={doc} />
          ))}
        </div>
      ) : (
        <div className="text-slate-400 text-sm">暂无文档</div>
      )}
    </div>
  )
}
