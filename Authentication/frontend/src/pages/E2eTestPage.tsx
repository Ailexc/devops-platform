import { DownOutlined, PlayCircleOutlined, RightOutlined, ThunderboltOutlined } from '@ant-design/icons'
import { App as AntApp, Button, Input, Space, Tag } from 'antd'
import { useEffect, useState } from 'react'
import { authApi } from '../api/client'
import { e2eScenes } from '../data/e2eScenes'
import type { E2eOutput, E2eSceneDef, RunCtx, StepOutput } from '../data/e2eScenes'

interface StepResult {
  name: string
  method: string
  api: string
  principle: string
  inputs: { label: string; value: string; kind?: 'text' | 'secret' }[]
  outputs: E2eOutput[]
  ok: boolean
}

const mask = (v: string): string =>
  v.length > 24 ? `${v.slice(0, 18)}…${v.slice(-6)}` : v

const isOk = (r: unknown): boolean =>
  !(r as { error?: string })?.error && (r as { status?: number })?.status !== undefined

export default function E2eTestPage() {
  const { message } = AntApp.useApp()
  const [token, setToken] = useState<string | null>(null)
  const [currentUser, setCurrentUser] = useState('')
  const [results, setResults] = useState<Record<string, StepResult[]>>({})
  const [runningId, setRunningId] = useState<string | null>(null)
  const [runningAll, setRunningAll] = useState(false)
  const [expandedId, setExpandedId] = useState<string | null>(null)

  const ctx: RunCtx = { token, setToken }

  useEffect(() => {
    authApi.me().then((r) => setCurrentUser(r.data.display_name || r.data.username)).catch(() => {})
  }, [])

  const runScene = async (scene: E2eSceneDef) => {
    setRunningId(scene.id)
    if (!token && scene.id !== 'login') {
      try {
        const { data } = await authApi.login('zhangsan', 'demo1234')
        setToken(data.access_token)
        ctx.token = data.access_token
      } catch {
        message.error('自动登录失败')
        setRunningId(null)
        return
      }
    }
    const steps: StepResult[] = []
    let prev: StepOutput | undefined
    for (const def of scene.steps) {
      try {
        const out = await def.run(ctx, prev)
        steps.push({
          name: def.name,
          method: def.method,
          api: def.api,
          principle: def.principle,
          inputs: def.inputs ?? [],
          outputs: def.extract ? def.extract(out.response) : [],
          ok: isOk(out.response),
        })
        prev = out
      } catch (e) {
        steps.push({
          name: def.name,
          method: def.method,
          api: def.api,
          principle: def.principle,
          inputs: def.inputs ?? [],
          outputs: [{ label: '错误', value: String(e), kind: 'warn' }],
          ok: false,
        })
      }
    }
    setResults((prevR) => ({ ...prevR, [scene.id]: steps }))
    setRunningId(null)
  }

  const runAll = async () => {
    setRunningAll(true)
    setResults({})
    for (const scene of e2eScenes) {
      await runScene(scene)
    }
    setRunningAll(false)
    message.success('全部场景执行完成')
  }

  const busy = runningId !== null || runningAll
  const toggle = (id: string) => setExpandedId((cur) => (cur === id ? null : id))

  return (
    <main className="profile-container" style={{ maxWidth: 1080 }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16, flexWrap: 'wrap', gap: 12 }}>
        <div>
          <h3 style={{ margin: 0 }}>SSO 可视化测试流程</h3>
          <span style={{ color: '#667085', fontSize: 13 }}>
            点击场景卡片查看说明并运行测试 —— 展示每一步的关键输入 / 输出与运作原理
          </span>
        </div>
        <Space>
          {currentUser && <Tag color="blue">当前用户：{currentUser}</Tag>}
          <Button type="primary" icon={<ThunderboltOutlined />} loading={runningAll} disabled={busy} onClick={runAll}>
            一键跑全部
          </Button>
        </Space>
      </div>

      {e2eScenes.map((scene) => {
        const sceneResult = results[scene.id]
        const passed = sceneResult?.every((s) => s.ok) ?? false
        const expanded = expandedId === scene.id
        const running = runningId === scene.id
        return (
          <div
            key={scene.id}
            style={{ background: '#fff', borderRadius: 12, border: '1px solid #e4e9f2', marginBottom: 12, overflow: 'hidden' }}
          >
            {/* 卡片头：点击展开 */}
            <div
              onClick={() => toggle(scene.id)}
              style={{ display: 'flex', alignItems: 'center', gap: 12, padding: '14px 18px', cursor: 'pointer' }}
            >
              {expanded ? <DownOutlined style={{ color: '#98a2b3' }} /> : <RightOutlined style={{ color: '#98a2b3' }} />}
              <div style={{ flex: 1 }}>
                <div style={{ fontWeight: 600, fontSize: 15 }}>{scene.name}</div>
                <div style={{ color: '#667085', fontSize: 13 }}>{scene.description}</div>
              </div>
              <span style={{ color: '#98a2b3', fontSize: 12, marginRight: 8 }}>{scene.steps.length} 步</span>
              {sceneResult && (
                <Tag color={passed ? 'success' : 'error'} style={{ marginRight: 8 }}>
                  {passed ? '✓ 全部通过' : '✕ 有失败'}
                </Tag>
              )}
              <Button
                size="small"
                type="primary"
                icon={<PlayCircleOutlined />}
                loading={running}
                disabled={busy}
                onClick={(e) => {
                  e.stopPropagation()
                  runScene(scene)
                }}
              >
                运行测试
              </Button>
            </div>

            {/* 展开详情 */}
            {expanded && (
              <div style={{ borderTop: '1px solid #eef0f4', padding: '16px 20px' }}>
                <div style={{ background: '#f8fafd', borderRadius: 10, padding: '12px 16px', marginBottom: 16, color: '#475467', fontSize: 14 }}>
                  📌 <b>场景说明：</b>{scene.intro}
                </div>

                {sceneResult && sceneResult.length > 0 ? (
                  <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
                    {sceneResult.map((s, i) => (
                      <div
                        key={i}
                        style={{
                          border: `1px solid ${s.ok ? '#c6f6d5' : '#fecaca'}`,
                          background: s.ok ? '#f6fef9' : '#fef6f6',
                          borderRadius: 10, padding: '14px 16px',
                        }}
                      >
                        <div style={{ display: 'flex', alignItems: 'center', gap: 8, flexWrap: 'wrap' }}>
                          <span style={{ fontWeight: 700, color: s.ok ? '#047857' : '#dc2626' }}>{s.ok ? '✓' : '✕'}</span>
                          <span style={{ fontWeight: 600, fontSize: 14 }}>{s.name}</span>
                          <Tag color="blue" style={{ marginLeft: 'auto' }}>{s.method}</Tag>
                          <code style={{ fontSize: 12 }}>{s.api}</code>
                        </div>

                        <div style={{ marginTop: 8, color: '#475467', fontSize: 13, lineHeight: 1.8 }}>
                          <b>📖 原理：</b>{s.principle}
                        </div>

                        {s.inputs.length > 0 && (
                          <div style={{ marginTop: 10 }}>
                            <div style={{ color: '#98a2b3', fontSize: 12, marginBottom: 6 }}>输入（关键参数）</div>
                            <div style={{ display: 'flex', gap: 10, flexWrap: 'wrap' }}>
                              {s.inputs.map((inp, j) => (
                                <Input
                                  key={j}
                                  style={{ width: 260 }}
                                  addonBefore={inp.label}
                                  value={inp.kind === 'secret' ? '••••••••••' : inp.value}
                                  disabled
                                />
                              ))}
                            </div>
                          </div>
                        )}

                        {s.outputs.length > 0 && (
                          <div style={{ marginTop: 10 }}>
                            <div style={{ color: '#98a2b3', fontSize: 12, marginBottom: 6 }}>输出（关键结果）</div>
                            <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
                              {s.outputs.map((o, j) => (
                                <div key={j} style={{ display: 'flex', gap: 10, alignItems: 'baseline', fontSize: 13 }}>
                                  <span style={{ color: '#667085', width: 150, flex: 'none' }}>{o.label}</span>
                                  <code
                                    style={{
                                      background: o.kind === 'warn' ? '#fff7ed' : '#eef2fa',
                                      color: o.kind === 'warn' ? '#b45309' : '#1d4ed8',
                                      padding: '3px 10px', borderRadius: 6, fontSize: 12, wordBreak: 'break-all',
                                    }}
                                  >
                                    {o.kind === 'secret' ? mask(o.value) : o.value}
                                  </code>
                                </div>
                              ))}
                            </div>
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                ) : (
                  <div style={{ textAlign: 'center', color: '#98a2b3', padding: 24 }}>
                    点击右上角「运行测试」查看每一步的输入 / 输出与原理说明
                  </div>
                )}
              </div>
            )}
          </div>
        )
      })}
    </main>
  )
}
