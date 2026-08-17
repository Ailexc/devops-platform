import { ArrowLeftOutlined } from '@ant-design/icons'
import { useEffect, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { getNextScene, getSceneById } from '../data/presentationScenes'
import type { PStep } from '../data/presentationScenes'

/* 横向流程示意图 */
function FlowVisual({ nodes, color }: { nodes: string[]; color: string }) {
  return (
    <div style={{ display: 'flex', alignItems: 'stretch', gap: 0, flexWrap: 'wrap' }}>
      {nodes.map((n, i) => (
        <div key={i} style={{ display: 'flex', alignItems: 'center' }}>
          <div
            style={{
              background: i === nodes.length - 1 ? color : '#f1f5fe',
              color: i === nodes.length - 1 ? '#fff' : color,
              border: `2px solid ${i === nodes.length - 1 ? color : '#c7d7ff'}`,
              borderRadius: 10, padding: '10px 14px', fontSize: 13, fontWeight: 600,
              minWidth: 96, textAlign: 'center',
            }}
          >
            {n}
          </div>
          {i < nodes.length - 1 && (
            <div style={{ color: color, fontSize: 18, padding: '0 6px', fontWeight: 700 }}>→</div>
          )}
        </div>
      ))}
    </div>
  )
}

/* 要点分块网格 */
function PointsGrid({ points, color }: { points: string[]; color: string }) {
  return (
    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit,minmax(180px,1fr))', gap: 12 }}>
      {points.map((p, i) => (
        <div
          key={i}
          style={{
            background: '#f8fafd', border: '1px solid #e4e9f2', borderRadius: 12, padding: '14px',
            display: 'flex', gap: 10, alignItems: 'flex-start',
          }}
        >
          <span style={{ width: 24, height: 24, borderRadius: 8, background: color, color: '#fff', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 12, fontWeight: 700, flex: 'none' }}>
            {i + 1}
          </span>
          <span style={{ color: '#344054', fontSize: 13, lineHeight: 1.6 }}>{p}</span>
        </div>
      ))}
    </div>
  )
}

export default function PresentationPlayerPage() {
  const { sceneId = '' } = useParams()
  const nav = useNavigate()
  const scene = getSceneById(sceneId)
  const [step, setStep] = useState(0)

  useEffect(() => {
    setStep(0)
  }, [sceneId])

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        nav('/presentation')
        return
      }
      if (!scene) return
      if (e.key === 'ArrowRight' || e.key === ' ') {
        e.preventDefault()
        if (step < scene.steps.length - 1) setStep(step + 1)
      } else if (e.key === 'ArrowLeft') {
        if (step > 0) setStep(step - 1)
      }
    }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [step, scene, nav])

  if (!scene) {
    return <div style={{ padding: 80, textAlign: 'center', color: '#667085' }}>场景不存在 <a onClick={() => nav('/presentation')}>返回目录</a></div>
  }

  // 钳制 step：切换场景瞬间 step 可能越界（旧场景最后一步 → 新场景步骤更少），
  // 用 safeStep 保证 current 永远有效，避免 undefined 渲染
  const safeStep = Math.min(step, scene.steps.length - 1)
  const current: PStep = scene.steps[safeStep]
  if (!current) return null

  const next = getNextScene(scene.id)
  const isLast = step === scene.steps.length - 1
  const color = scene.themeColor

  const gotoNextScene = () => {
    if (!next) return
    setStep(0)
    nav(`/presentation/${next.id}`)
  }

  return (
    <main
      key={scene.id + step}
      style={{
        height: 'calc(100vh - 56px)', display: 'flex', flexDirection: 'column',
        background: 'linear-gradient(135deg,#f5f7fa,#e4ecf7)', padding: '18px 24px', boxSizing: 'border-box',
        animation: 'fadeSlide .3s ease',
      }}
    >
      {/* 顶栏 */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: 8 }}>
        <button onClick={() => nav('/presentation')} style={{ border: 'none', background: 'transparent', color: '#475467', cursor: 'pointer', fontSize: 14 }}>
          <ArrowLeftOutlined /> 返回目录
        </button>
        <span style={{ color: '#667085', fontSize: 13 }}>
          {scene.title} · 第 {safeStep + 1} / {scene.steps.length} 步
        </span>
      </div>

      {/* 进度条 */}
      <div style={{ background: '#dde3ee', borderRadius: 4, height: 6, margin: '12px 0 16px', overflow: 'hidden' }}>
        <div style={{ height: '100%', background: color, borderRadius: 4, width: `${((safeStep + 1) / scene.steps.length) * 100}%`, transition: 'width .3s' }} />
      </div>

      {/* 主体：左讲解 + 右图例 */}
      <div style={{ flex: 1, display: 'flex', gap: 20, minHeight: 0 }}>
        {/* 左：STEP / 标题 / 讲解词 */}
        <div
          style={{
            flex: '1 1 40%', background: '#fff', borderRadius: 16, padding: '28px 32px',
            boxShadow: '0 8px 28px rgba(16,24,40,.08)', display: 'flex', flexDirection: 'column', overflow: 'auto',
          }}
        >
          <div style={{ fontSize: 13, color, fontWeight: 700, marginBottom: 8 }}>STEP {step + 1}</div>
          <h1 style={{ margin: '0 0 18px', fontSize: 26, lineHeight: 1.4 }}>{current.title}</h1>
          <p style={{ color: '#475467', fontSize: 15, lineHeight: 1.95, margin: 0, flex: 1 }}>{current.narration}</p>
          {current.highlight && (
            <div style={{ background: `${color}14`, color, borderRadius: 10, padding: '12px 16px', fontSize: 14, fontWeight: 700, marginTop: 20 }}>
              ⭐ {current.highlight}
            </div>
          )}
        </div>

        {/* 右：图例 + 要点分块 */}
        <div style={{ flex: '1 1 60%', display: 'flex', flexDirection: 'column', gap: 16, minHeight: 0 }}>
          {current.flow && current.flow.length > 0 && (
            <div style={{ background: '#fff', borderRadius: 16, padding: '20px 24px', boxShadow: '0 8px 28px rgba(16,24,40,.08)' }}>
              <div style={{ color: '#667085', fontSize: 13, marginBottom: 12, fontWeight: 600 }}>🧭 流程示意图</div>
              <FlowVisual nodes={current.flow} color={color} />
            </div>
          )}
          {current.points && current.points.length > 0 && (
            <div style={{ background: '#fff', borderRadius: 16, padding: '20px 24px', boxShadow: '0 8px 28px rgba(16,24,40,.08)', flex: 1, overflow: 'auto' }}>
              <div style={{ color: '#667085', fontSize: 13, marginBottom: 12, fontWeight: 600 }}>📌 要点拆解</div>
              <PointsGrid points={current.points} color={color} />
            </div>
          )}
        </div>
      </div>

      {/* 底部操作栏 */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: 16, flexWrap: 'wrap', gap: 10 }}>
        <button
          onClick={() => step > 0 && setStep(step - 1)}
          disabled={step === 0}
          style={{ border: '1px solid #d0d5dd', background: '#fff', padding: '10px 26px', borderRadius: 8, cursor: step === 0 ? 'default' : 'pointer', color: step === 0 ? '#c0c8d4' : '#344054' }}
        >
          ← 上一步
        </button>
        <span style={{ color: '#98a2b3', fontSize: 12 }}>← → 翻页 · Space 下一步 · ESC 返回</span>
        {isLast ? (
          next ? (
            <button onClick={gotoNextScene} style={{ border: 'none', background: color, color: '#fff', padding: '10px 26px', borderRadius: 8, cursor: 'pointer' }}>
              下一场景：{next.title} →
            </button>
          ) : (
            <button onClick={() => nav('/presentation')} style={{ border: 'none', background: color, color: '#fff', padding: '10px 26px', borderRadius: 8, cursor: 'pointer' }}>
              完成，返回目录
            </button>
          )
        ) : (
          <button onClick={() => setStep(step + 1)} style={{ border: 'none', background: color, color: '#fff', padding: '10px 26px', borderRadius: 8, cursor: 'pointer' }}>
            下一步 →
          </button>
        )}
      </div>

      <style>{`
        @keyframes fadeSlide { from { opacity: 0; transform: translateX(14px); } to { opacity: 1; transform: none; } }
        @media (max-width: 900px) { main > div:nth-child(3) { flex-direction: column !important; } }
      `}</style>
    </main>
  )
}
