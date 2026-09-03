import { ArrowLeftOutlined } from '@ant-design/icons'
import { useEffect, useRef, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { systemDocsApi } from '../api/client'
import type { SystemDocsIndex } from '../types'

/** 文档排版样式（统一由前端提供，文档片段保持语义化） */
const DOC_CSS = `
.sysdoc { color:#334155; font-size:14px; line-height:1.85; }
.sysdoc h2 { font-size:20px; color:#1e293b; margin:34px 0 12px; padding-bottom:10px; border-bottom:1px solid #eef1f5; font-weight:700; }
.sysdoc h2:first-child { margin-top:0; }
.sysdoc h3 { font-size:16px; color:#1e293b; margin:24px 0 8px; font-weight:700; }
.sysdoc p { margin:10px 0; }
.sysdoc strong { color:#1e293b; font-weight:700; }
.sysdoc code { background:#eef2f7; color:#0f4c81; padding:2px 6px; border-radius:5px; font-size:12.5px; font-family:'SFMono-Regular',Consolas,'Liberation Mono',monospace; }
.sysdoc pre { background:#0f172a; color:#e2e8f0; padding:14px 16px; border-radius:10px; overflow:auto; margin:12px 0; line-height:1.6; }
.sysdoc pre code { background:transparent; color:inherit; padding:0; font-size:12.5px; }
.sysdoc ul, .sysdoc ol { margin:8px 0; padding-left:22px; }
.sysdoc li { margin:5px 0; }
.sysdoc table { width:100%; border-collapse:collapse; margin:14px 0; font-size:13px; }
.sysdoc th { background:#f1f5f9; color:#334155; font-weight:700; text-align:left; padding:9px 12px; border:1px solid #e2e8f0; }
.sysdoc td { padding:8px 12px; border:1px solid #e8edf3; color:#475569; vertical-align:top; }
.sysdoc tr:nth-child(even) td { background:#fafbfd; }
.sysdoc .note { background:#eff6ff; border-left:4px solid #3b82f6; border-radius:0 10px 10px 0; padding:12px 16px; margin:14px 0; font-size:13.5px; color:#1e3a5f; }
.sysdoc .note strong { color:#1d4ed8; }
.sysdoc .warn { background:#fef2f2; border-left:4px solid #ef4444; border-radius:0 10px 10px 0; padding:12px 16px; margin:14px 0; font-size:13.5px; color:#7f1d1d; }
.sysdoc .warn strong { color:#b91c1c; }
.sysdoc .flow { display:flex; flex-wrap:wrap; gap:8px; align-items:center; background:#f8fafc; border:1px solid #e8edf3; border-radius:10px; padding:12px 14px; margin:12px 0; }
.sysdoc .flow .step { background:#fff; border:1px solid #dbe4ee; border-radius:8px; padding:6px 12px; font-size:12.5px; font-weight:600; color:#334155; }
.sysdoc .flow .arrow { color:#94a3b8; font-weight:700; }
.sysdoc a.doc-link { color:#2563eb; text-decoration:underline; cursor:pointer; }
.sysdoc a.doc-link:hover { color:#1d4ed8; }
@media (max-width: 720px) {
  .sysdoc { font-size:13.5px; }
  .sysdoc h2 { font-size:18px; }
  .sysdoc table { font-size:12px; }
}
`

/** 简单清理 HTML 片段：移除脚本/事件属性，防注入（文档虽为自建，纵深防御） */
function sanitizeHtml(html: string): string {
  const doc = new DOMParser().parseFromString(html, 'text/html')
  doc.querySelectorAll('script,style,iframe,object,embed,link,meta').forEach((el) => el.remove())
  doc.querySelectorAll('*').forEach((el) => {
    for (const attr of Array.from(el.attributes)) {
      const name = attr.name.toLowerCase()
      if (name.startsWith('on') || (name === 'href' && attr.value.trim().toLowerCase().startsWith('javascript:'))) {
        el.removeAttribute(attr.name)
      }
    }
  })
  return doc.body.innerHTML
}

/** 中文锚点 slug：优先用标题自带 id，否则生成 */
function slugify(text: string): string {
  const s = text.trim().toLowerCase().replace(/[^\w\u4e00-\u9fa5-]+/g, '-').replace(/^-+|-+$/g, '')
  return s || 'sec'
}

interface TocItem {
  id: string
  text: string
  level: 2 | 3
}

export default function SystemDocsReaderPage() {
  const { docId = '' } = useParams()
  const nav = useNavigate()
  const containerRef = useRef<HTMLDivElement>(null)
  const [meta, setMeta] = useState<SystemDocsIndex | null>(null)
  const [html, setHtml] = useState('')
  const [title, setTitle] = useState('')
  const [toc, setToc] = useState<TocItem[]>([])
  const [activeId, setActiveId] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(true)

  // 加载文档清单 + 指定文档内容
  useEffect(() => {
    setLoading(true)
    setError('')
    setHtml('')
    setToc([])
    setActiveId('')
    Promise.all([systemDocsApi.index(), systemDocsApi.doc(docId)])
      .then(([idxRes, docRes]) => {
        setMeta(idxRes.data)
        const item = idxRes.data.docs.find((d) => d.id === docId)
        if (!item) {
          setError('文档不存在')
          return
        }
        setTitle(item.title)
        setHtml(sanitizeHtml(docRes.data))
      })
      .catch(() => setError('文档加载失败，请稍后重试'))
      .finally(() => setLoading(false))
  }, [docId])

  // 注入完成后解析标题生成目录
  useEffect(() => {
    if (!html || !containerRef.current) return
    const root = containerRef.current
    const headings = Array.from(root.querySelectorAll<HTMLElement>('h2, h3'))
    const items: TocItem[] = []
    headings.forEach((h, i) => {
      const level = h.tagName.toLowerCase() === 'h2' ? 2 : 3
      if (!h.id) h.id = `${slugify(h.textContent || '')}-${i}`
      items.push({ id: h.id, text: h.textContent?.trim() || '', level })
    })
    setToc(items)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [html])

  // 滚动高亮跟随：监听滚动，同步计算视口内最靠上的标题作为当前章节
  useEffect(() => {
    if (!html || !containerRef.current) return
    const root = containerRef.current
    const compute = () => {
      const headings = Array.from(root.querySelectorAll<HTMLElement>('h2, h3'))
      const offset = 84 // 顶栏下方判定线
      let current = ''
      for (const h of headings) {
        if (h.getBoundingClientRect().top <= offset) current = h.id
        else break
      }
      setActiveId((prev) => (prev === current ? prev : current))
    }
    compute()
    window.addEventListener('scroll', compute, { passive: true })
    return () => window.removeEventListener('scroll', compute)
  }, [html])

  // 文档内跨文档链接：/system-docs/{id}（事件委托，容器级绑定，稳健）
  useEffect(() => {
    const root = containerRef.current
    if (!root) return
    const handler = (e: MouseEvent) => {
      const t = e.target as HTMLElement
      const link = t.closest('a.doc-link') as HTMLAnchorElement | null
      if (!link) return
      e.preventDefault()
      const docId = link.getAttribute('data-doc')
      if (docId) nav(`/docs/${docId}`)
    }
    root.addEventListener('click', handler)
    return () => root.removeEventListener('click', handler)
  }, [html, nav])

  // 目录点击跳转：setInterval 驱动的平滑滚动（不依赖 rAF，全环境可用）
  const jumpTo = (id: string) => {
    setActiveId(id)
    const el = document.getElementById(id)
    if (!el) return
    const startY = window.scrollY
    const dist = el.getBoundingClientRect().top - 16
    const dur = Math.min(560, Math.max(240, Math.abs(dist) * 0.3))
    const t0 = performance.now()
    const timer = window.setInterval(() => {
      const p = Math.min(1, (performance.now() - t0) / dur)
      const ease = p < 0.5 ? 2 * p * p : 1 - Math.pow(-2 * p + 2, 2) / 2
      window.scrollTo(0, startY + dist * ease)
      if (p >= 1) window.clearInterval(timer)
    }, 16)
  }

  const currentMeta = meta?.docs.find((d) => d.id === docId)
  const category = meta?.categories.find((c) => c.id === currentMeta?.category)

  return (
    <main style={{ minHeight: 'calc(100vh - 56px)', background: '#f5f7fa', padding: '24px 28px' }}>
      <style>{DOC_CSS}</style>
      <div style={{ maxWidth: 1160, margin: '0 auto' }}>
        {/* 顶栏 */}
        <div style={{ display: 'flex', alignItems: 'center', gap: 14, marginBottom: 18, flexWrap: 'wrap' }}>
          <button onClick={() => nav('/docs')} style={{ border: '1px solid #d0d5dd', background: '#fff', borderRadius: 8, padding: '8px 14px', cursor: 'pointer', color: '#344054', fontSize: 13, display: 'flex', alignItems: 'center', gap: 6 }}>
            <ArrowLeftOutlined /> 返回文档库
          </button>
          {currentMeta && (
            <span style={{ background: `${currentMeta.color}12`, color: currentMeta.color, padding: '4px 12px', borderRadius: 20, fontSize: 12, fontWeight: 700 }}>
              {currentMeta.icon} {category?.name ?? ''}
            </span>
          )}
          <span style={{ fontSize: 16, fontWeight: 700, color: '#1e293b' }}>{title}</span>
        </div>

        {loading && <div style={{ textAlign: 'center', padding: 80, color: '#98a2b3' }}>加载中…</div>}
        {error && <div style={{ textAlign: 'center', padding: 80, color: '#667085' }}>{error} <a onClick={() => nav('/docs')}>返回文档库</a></div>}

        {!loading && !error && (
          <div style={{ display: 'flex', gap: 24, alignItems: 'flex-start' }}>
            {/* 正文 */}
            <article
              ref={containerRef}
              className="sysdoc"
              style={{ flex: 1, minWidth: 0, background: '#fff', borderRadius: 14, padding: '32px 40px', boxShadow: '0 2px 10px rgba(16,24,40,.05)', border: '1px solid #e6ebf2' }}
              dangerouslySetInnerHTML={{ __html: html }}
            />

            {/* 目录 */}
            {toc.length > 0 && (
              <aside style={{ width: 250, flex: 'none', position: 'sticky', top: 24, maxHeight: 'calc(100vh - 120px)', overflow: 'auto', background: '#fff', borderRadius: 14, padding: '16px 14px', border: '1px solid #e6ebf2', boxShadow: '0 2px 10px rgba(16,24,40,.04)' }}>
                <div style={{ fontSize: 12, fontWeight: 700, color: '#98a2b3', letterSpacing: 1, marginBottom: 10, padding: '0 6px' }}>本页目录</div>
                <div style={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
                  {toc.map((item) => (
                    <button
                      key={item.id}
                      onClick={() => jumpTo(item.id)}
                      style={{
                        textAlign: 'left', border: 'none', background: 'transparent', cursor: 'pointer',
                        padding: item.level === 2 ? '6px 8px' : '5px 8px 5px 20px',
                        fontSize: item.level === 2 ? 13 : 12,
                        color: activeId === item.id ? '#1d5fd6' : '#475569',
                        fontWeight: activeId === item.id ? 700 : 400,
                        borderLeft: activeId === item.id ? '3px solid #1d5fd6' : '3px solid transparent',
                        borderRadius: '0 6px 6px 0', lineHeight: 1.4, width: '100%',
                      }}
                    >
                      {item.text}
                    </button>
                  ))}
                </div>
              </aside>
            )}
          </div>
        )}
      </div>
    </main>
  )
}
