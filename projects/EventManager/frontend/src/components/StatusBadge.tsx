const statusConfig: Record<string, { bg: string; dot: string; label: string }> = {
  pending:    { bg: 'bg-amber-50 text-amber-700', dot: 'bg-amber-400', label: '待处理' },
  processing: { bg: 'bg-blue-50 text-blue-700',   dot: 'bg-blue-400 animate-pulse', label: '处理中' },
  completed:  { bg: 'bg-green-50 text-green-700',  dot: 'bg-green-400', label: '已完成' },
  failed:     { bg: 'bg-red-50 text-red-700',      dot: 'bg-red-400', label: '失败' },
  dlq:        { bg: 'bg-purple-50 text-purple-700', dot: 'bg-purple-400', label: '死信' },
}

export default function StatusBadge({ status }: { status: string }) {
  const cfg = statusConfig[status] ?? statusConfig.pending
  return (
    <span className={`inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-medium ${cfg.bg}`}>
      <span className={`w-1.5 h-1.5 rounded-full ${cfg.dot}`} />
      {cfg.label}
    </span>
  )
}
