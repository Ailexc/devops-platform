import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { systemDocsApi } from '../api/client'
import type { SystemDocsIndex } from '../types'

export default function SystemDocsHubPage() {
  const nav = useNavigate()
  const [index, setIndex] = useState<SystemDocsIndex | null>(null)
  const [error, setError] = useState('')

  useEffect(() => {
    systemDocsApi
      .index()
      .then((res) => setIndex(res.data))
      .catch(() => setError('文档库加载失败，请稍后重试'))
  }, [])

  if (error) {
    return (
      <main style={{ minHeight: 'calc(100vh - 56px)', background: '#f5f7fa', padding: 80, textAlign: 'center', color: '#667085' }}>
        {error}
      </main>
    )
  }

  const total = index?.docs.length ?? 0
  const categories = index?.categories ?? []

  return (
    <main style={{ minHeight: 'calc(100vh - 56px)', background: 'linear-gradient(135deg,#f5f7fa,#e8eef7)', padding: '40px 20px' }}>
      <div style={{ maxWidth: 1000, margin: '0 auto' }}>
        <div style={{ textAlign: 'center', marginBottom: 36 }}>
          <div style={{ fontSize: 46 }}>📚</div>
          <h1 style={{ margin: '8px 0', fontSize: 30 }}>系统文档</h1>
          <p style={{ color: '#667085', margin: 0, fontSize: 14 }}>
            概念 · 架构 · 接入 · 协议 · 安全 —— 系统化讲解本项目每一层设计
          </p>
          <div style={{ marginTop: 12 }}>
            <span style={{ display: 'inline-block', background: '#eef2fa', borderRadius: 20, padding: '4px 14px', fontSize: 13, color: '#475467', margin: '0 6px' }}>
              {total} 篇文档
            </span>
            <span style={{ display: 'inline-block', background: '#eef2fa', borderRadius: 20, padding: '4px 14px', fontSize: 13, color: '#475467', margin: '0 6px' }}>
              {categories.length} 个分类
            </span>
          </div>
        </div>

        {index &&
          categories.map((cat) => {
            const docs = index.docs.filter((d) => d.category === cat.id).sort((a, b) => a.order - b.order)
            if (docs.length === 0) return null
            return (
              <section key={cat.id} style={{ marginBottom: 32 }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 14 }}>
                  <span style={{ width: 4, height: 18, borderRadius: 2, background: cat.color }} />
                  <h2 style={{ margin: 0, fontSize: 17, color: '#1e293b' }}>{cat.name}</h2>
                  <span style={{ fontSize: 12, color: '#98a2b3' }}>{docs.length} 篇</span>
                  <div style={{ flex: 1, height: 1, background: 'linear-gradient(to right, #e2e8f0, transparent)' }} />
                </div>
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit,minmax(280px,1fr))', gap: 14 }}>
                  {docs.map((doc) => (
                    <div
                      key={doc.id}
                      onClick={() => nav(`/docs/${doc.id}`)}
                      style={{
                        background: '#fff', borderRadius: 14, padding: 18, cursor: 'pointer',
                        border: '1px solid #e6ebf2', borderTop: `4px solid ${doc.color}`,
                        boxShadow: '0 2px 10px rgba(16,24,40,.05)', transition: 'transform .15s ease, box-shadow .15s ease',
                      }}
                      onMouseEnter={(e) => {
                        ;(e.currentTarget as HTMLElement).style.transform = 'translateY(-3px)'
                        ;(e.currentTarget as HTMLElement).style.boxShadow = '0 10px 24px rgba(16,24,40,.10)'
                      }}
                      onMouseLeave={(e) => {
                        ;(e.currentTarget as HTMLElement).style.transform = 'none'
                        ;(e.currentTarget as HTMLElement).style.boxShadow = '0 2px 10px rgba(16,24,40,.05)'
                      }}
                    >
                      <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 10 }}>
                        <span style={{ fontSize: 26, flex: 'none' }}>{doc.icon}</span>
                        <div style={{ flex: 1, minWidth: 0 }}>
                          <div style={{ fontSize: 11, color: doc.color, fontWeight: 700, letterSpacing: 0.5 }}>{cat.name.toUpperCase()}</div>
                          <h3 style={{ margin: '2px 0 0', fontSize: 15.5, color: '#1e293b' }}>{doc.title}</h3>
                        </div>
                      </div>
                      <p style={{ margin: 0, color: '#667085', fontSize: 12.5, lineHeight: 1.6, minHeight: 40 }}>{doc.description}</p>
                      <div style={{ marginTop: 10, color: doc.color, fontSize: 13, fontWeight: 600 }}>阅读文档 →</div>
                    </div>
                  ))}
                </div>
              </section>
            )
          })}
      </div>
    </main>
  )
}
