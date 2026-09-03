import { useNavigate } from 'react-router-dom'
import { scenes } from '../data/presentationScenes'
import { SceneThumbnail } from '../components/PresentationVisuals'

export default function PresentationHubPage() {
  const nav = useNavigate()
  const totalSteps = scenes.reduce((sum, s) => sum + s.steps.length, 0)

  return (
    <main style={{ minHeight: 'calc(100vh - 56px)', background: 'linear-gradient(135deg,#f5f7fa,#e4ecf7)', padding: '40px 20px' }}>
      <div style={{ maxWidth: 900, margin: '0 auto' }}>
        <div style={{ textAlign: 'center', marginBottom: 40 }}>
          <div style={{ fontSize: 48 }}>🎬</div>
          <h1 style={{ margin: '8px 0', fontSize: 32 }}>系统宣讲</h1>
          <p style={{ color: '#667085', margin: 0 }}>
            统一门户 · 登录认证 · SSO 多系统统一访问 —— 全方位展示系统能力
          </p>
          <div style={{ marginTop: 12 }}>
            <span style={{ display: 'inline-block', background: '#eef2fa', borderRadius: 20, padding: '4px 14px', fontSize: 13, color: '#475467', margin: '0 6px' }}>
              {scenes.length} 个场景
            </span>
            <span style={{ display: 'inline-block', background: '#eef2fa', borderRadius: 20, padding: '4px 14px', fontSize: 13, color: '#475467', margin: '0 6px' }}>
              {totalSteps} 个步骤
            </span>
            <span style={{ display: 'inline-block', background: '#eef2fa', borderRadius: 20, padding: '4px 14px', fontSize: 13, color: '#475467', margin: '0 6px' }}>
              ~10 分钟
            </span>
          </div>
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit,minmax(240px,1fr))', gap: 18 }}>
          {scenes.map((scene, index) => (
            <div
              key={scene.id}
              onClick={() => nav(`/presentation/${scene.id}`)}
              style={{
                background: '#fff', borderRadius: 14, padding: 20, cursor: 'pointer',
                borderTop: `4px solid ${scene.themeColor}`,
                boxShadow: '0 2px 10px rgba(16,24,40,.06)',
                transition: 'transform .15s ease, box-shadow .15s ease',
              }}
              onMouseEnter={(e) => {
                ;(e.currentTarget as HTMLElement).style.transform = 'translateY(-3px)'
                ;(e.currentTarget as HTMLElement).style.boxShadow = '0 10px 24px rgba(16,24,40,.12)'
              }}
              onMouseLeave={(e) => {
                ;(e.currentTarget as HTMLElement).style.transform = 'none'
                ;(e.currentTarget as HTMLElement).style.boxShadow = '0 2px 10px rgba(16,24,40,.06)'
              }}
            >
              <div style={{ display: 'flex', alignItems: 'flex-start', gap: 12, marginBottom: 10 }}>
                <SceneThumbnail sceneId={scene.id} color={scene.themeColor} />
                <div style={{ flex: 1 }}>
                  <div style={{ fontSize: 11, color: '#98a2b3', fontWeight: 600 }}>{String(index + 1).padStart(2, '0')} / {String(scenes.length).padStart(2, '0')}</div>
                  <h3 style={{ margin: '2px 0 4px', fontSize: 16 }}>{scene.title}</h3>
                </div>
              </div>
              <p style={{ margin: 0, color: '#667085', fontSize: 13, minHeight: 36, lineHeight: 1.5 }}>{scene.description}</p>
              <div style={{ marginTop: 12, display: 'flex', gap: 12, fontSize: 12, color: '#98a2b3' }}>
                <span>🕐 {scene.duration}</span>
                <span>📋 {scene.steps.length} 步</span>
              </div>
              <div style={{ marginTop: 8, color: scene.themeColor, fontSize: 13, fontWeight: 600 }}>开始演示 →</div>
            </div>
          ))}
        </div>

        <div style={{ textAlign: 'center', marginTop: 28, color: '#98a2b3', fontSize: 13 }}>
          <span style={{ margin: '0 10px' }}>← → 翻页</span>
          <span style={{ margin: '0 10px' }}>Space 下一步</span>
          <span style={{ margin: '0 10px' }}>ESC 返回目录</span>
        </div>
      </div>
    </main>
  )
}
