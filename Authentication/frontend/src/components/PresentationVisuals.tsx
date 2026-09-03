/**
 * 系统宣讲 —— 专业可视化组件（SVG 架构图 / 时序图）
 * 对齐 OIDC 标准改造后的现状：门户 SPA+BFF、认证中心 OIDC Provider、PostgreSQL、PKCE。
 */

import React from 'react'

/* ============ 通用 SVG 原子组件 ============ */

function Box({
  x, y, w, h, title, tech, desc, color = '#1d5fd6', active = true,
}: {
  x: number; y: number; w: number; h: number
  title: string; tech?: string; desc?: string
  color?: string; active?: boolean
}) {
  return (
    <g>
      <rect
        x={x} y={y} width={w} height={h} rx={8}
        fill={active ? '#fff' : '#f8fafc'}
        stroke={active ? color : '#cbd5e1'}
        strokeWidth={active ? 2 : 1}
        filter={active ? 'url(#shadow)' : undefined}
      />
      <rect x={x} y={y} width={4} height={h} rx={2} fill={color} opacity={active ? 1 : 0.3} />
      <text x={x + 14} y={y + 22} fontSize={13} fontWeight={700} fill="#1e293b">{title}</text>
      {tech && <text x={x + 14} y={y + 40} fontSize={10} fill={color} fontWeight={600}>{tech}</text>}
      {desc && <text x={x + 14} y={y + 56} fontSize={9.5} fill="#64748b">{desc}</text>}
    </g>
  )
}

function LayerBox({ x, y, w, h, label, color }: { x: number; y: number; w: number; h: number; label: string; color: string }) {
  return (
    <g>
      <rect x={x} y={y} width={w} height={h} rx={10} fill={`${color}08`} stroke={color} strokeWidth={1} strokeDasharray="6 4" />
      <rect x={x + 12} y={y - 10} width={label.length * 12 + 16} height={20} rx={4} fill={color} />
      <text x={x + 20} y={y + 4} fontSize={11} fontWeight={700} fill="#fff">{label}</text>
    </g>
  )
}

function Arrow({ x1, y1, x2, y2, label, color = '#64748b', dashed = false }: {
  x1: number; y1: number; x2: number; y2: number
  label?: string; color?: string; dashed?: boolean
}) {
  const midX = (x1 + x2) / 2
  const midY = (y1 + y2) / 2
  return (
    <g>
      <defs>
        <marker id={`arrow-${color.replace('#', '')}`} markerWidth="8" markerHeight="6" refX="7" refY="3" orient="auto">
          <polygon points="0 0, 8 3, 0 6" fill={color} />
        </marker>
      </defs>
      <line x1={x1} y1={y1} x2={x2} y2={y2} stroke={color} strokeWidth={1.5}
        strokeDasharray={dashed ? '5 3' : undefined}
        markerEnd={`url(#arrow-${color.replace('#', '')})`} />
      {label && (
        <g>
          <rect x={midX - label.length * 5 - 4} y={midY - 8} width={label.length * 10 + 8} height={16} rx={4} fill="#fff" stroke={color} strokeWidth={0.5} />
          <text x={midX} y={midY + 3} fontSize={9} fill={color} textAnchor="middle" fontWeight={600}>{label}</text>
        </g>
      )}
    </g>
  )
}

function SectionTitle({ icon, text, color }: { icon: string; text: string; color: string }) {
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 10 }}>
      <span style={{ fontSize: 15 }}>{icon}</span>
      <span style={{ fontSize: 13, fontWeight: 700, color: '#1e293b' }}>{text}</span>
      <div style={{ flex: 1, height: 1, background: `linear-gradient(to right, ${color}40, transparent)` }} />
    </div>
  )
}

function Wrap({ children, title, color, icon }: { children: React.ReactNode; title: string; color: string; icon: string }) {
  return (
    <div style={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
      <SectionTitle icon={icon} text={title} color={color} />
      <div style={{ flex: 1, background: '#fff', borderRadius: 12, padding: 8, border: '1px solid #e2e8f0', overflow: 'auto', minHeight: 0 }}>
        {children}
      </div>
    </div>
  )
}

const SHADOW = (
  <defs>
    <filter id="shadow" x="-10%" y="-10%" width="120%" height="120%">
      <feDropShadow dx="0" dy="2" stdDeviation="3" floodOpacity="0.1" />
    </filter>
  </defs>
)

/* ============ 场景1：系统概览 ============ */

export function OverviewVisual({ step, color }: { step: number; color: string }) {
  if (step === 0) {
    return (
      <Wrap title="项目定位 · 三大核心 + 三种接入" color={color} icon="🏗️">
        <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit,minmax(180px,1fr))', gap: 10 }}>
            {[
              { icon: '🏠', t: '统一门户', d: 'React SPA + BFF（OIDC 客户端）', c: '#3b82f6' },
              { icon: '🔑', t: '认证中心', d: '标准 OIDC Provider（FastAPI）', c: '#10b981' },
              { icon: '🛡️', t: '统一网关', d: 'Traefik forwardAuth 统一鉴权', c: '#f59e0b' },
            ].map((i) => (
              <div key={i.t} style={{ background: '#fff', border: `1px solid ${i.c}35`, borderTop: `3px solid ${i.c}`, borderRadius: 10, padding: '12px 14px' }}>
                <div style={{ fontSize: 20 }}>{i.icon}</div>
                <div style={{ fontSize: 13, fontWeight: 700, color: '#1e293b', margin: '4px 0 2px' }}>{i.t}</div>
                <div style={{ fontSize: 11, color: '#64748b', lineHeight: 1.5 }}>{i.d}</div>
              </div>
            ))}
          </div>
          <div style={{ background: `${color}0d`, border: `1px solid ${color}30`, borderRadius: 10, padding: '10px 14px' }}>
            <div style={{ fontSize: 12, fontWeight: 700, color: '#1e293b', marginBottom: 6 }}>📦 业务系统三种接入方式</div>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit,minmax(150px,1fr))', gap: 8 }}>
              {[
                { t: '经网关 forwardAuth', d: '零鉴权代码', c: '#10b981' },
                { t: '直连 JWKS 验签', d: '本地验签不回源', c: '#8b5cf6' },
                { t: 'OIDC 客户端', d: '标准协议换 token', c: '#f59e0b' },
              ].map((i) => (
                <div key={i.t} style={{ background: `${i.c}0d`, border: `1px solid ${i.c}35`, borderRadius: 8, padding: '8px 10px' }}>
                  <div style={{ fontSize: 11.5, fontWeight: 700, color: '#334155' }}>{i.t}</div>
                  <div style={{ fontSize: 10, color: '#64748b', marginTop: 2 }}>{i.d}</div>
                </div>
              ))}
            </div>
          </div>
          <div style={{ fontSize: 11, color: '#475569', lineHeight: 1.7 }}>
            💡 <b>核心卖点：</b>不再是自己拼的私有协议，而是 <b style={{ color }}>标准 OAuth 2.1 授权码 + PKCE + OIDC</b>——门户自身就是 OIDC 客户端（通过 BFF），业务系统可按标准协议接入，也可走内部统一 JWT 链路（网关 / 直连）。
          </div>
        </div>
      </Wrap>
    )
  }

  return (
    <Wrap title="整体架构 · 门户 BFF + OIDC Provider + 网关" color={color} icon="🏗️">
      <svg viewBox="0 0 720 430" style={{ width: '100%', height: '100%' }}>
        {SHADOW}
        {/* 左列：用户 */}
        <Box x={30} y={140} w={150} h={76} title="用户浏览器" tech="React SPA" desc="HttpOnly 会话 Cookie" color={color} />
        {/* 中列：门户 SPA + BFF + 认证中心 + 身份源（纵向登录链路） */}
        <Box x={250} y={30} w={170} h={60} title="门户 SPA" tech="React 19 + antd" desc="应用广场·宣讲·文档" color={color} active={step >= 1} />
        <Box x={250} y={118} w={170} h={60} title="门户 BFF" tech="portal.py" desc="OIDC 客户端·会话" color="#3b82f6" active={step >= 1} />
        <Box x={250} y={214} w={170} h={82} title="认证中心" tech="OIDC Provider" desc="authorize·token·userinfo" color="#10b981" active={step >= 1} />
        <Box x={250} y={326} w={170} h={42} title="身份源" tech="Local 默认 · LDAP/Okta 可选" color="#ef4444" />
        {/* 右列：网关 + 业务系统（纵向服务链路） */}
        <Box x={480} y={52} w={210} h={66} title="统一网关" tech="Traefik forwardAuth" desc="JWT 验签 · 注入身份" color="#f59e0b" active={step >= 1} />
        <LayerBox x={480} y={154} w={210} h={222} label="业务系统" color="#8b5cf6" />
        <Box x={492} y={174} w={186} h={58} title="经网关接入" tech="forwardAuth" desc="零鉴权代码" color="#10b981" />
        <Box x={492} y={246} w={186} h={58} title="直连自验签" tech="JWKS 本地验签" desc="不回源 · 高可用" color="#8b5cf6" />
        <Box x={492} y={318} w={186} h={58} title="OIDC 客户端" tech="PKCE 授权码" desc="code 换 token" color="#f59e0b" />
        {/* 连接线：纵向登录链路 + 列间横向链路（箭头全走空隙，不穿盒子） */}
        <Arrow x1={180} y1={160} x2={250} y2={70} label="访问" color={color} />
        <Arrow x1={335} y1={90} x2={335} y2={118} label="OIDC 授权码+PKCE" color="#3b82f6" />
        <Arrow x1={335} y1={178} x2={335} y2={214} label="换 token / userinfo" color="#10b981" />
        <Arrow x1={335} y1={296} x2={335} y2={326} label="身份校验" color="#ef4444" />
        <Arrow x1={420} y1={250} x2={480} y2={105} label="JWKS" color="#f59e0b" dashed />
        <Arrow x1={180} y1={215} x2={480} y2={100} color="#ef4444" />
        <Arrow x1={585} y1={118} x2={585} y2={174} label="forwardAuth" color={color} />
        {/* 底部说明 */}
        <rect x={30} y={404} width={660} height={22} rx={8} fill={`${color}0d`} stroke={`${color}30`} />
        <text x={46} y={419} fontSize={11} fill="#334155">
          核心：<tspan fontWeight={700} fill={color}>OIDC + PKCE</tspan> 标准登录 · <tspan fontWeight={700} fill="#3b82f6">BFF</tspan> 会话 · <tspan fontWeight={700} fill={color}>统一 JWT</tspan> 业务链路
        </text>
      </svg>
    </Wrap>
  )
}

/* ============ 场景2：架构设计 ============ */

export function ArchitectureVisual({ step, color }: { step: number; color: string }) {
  if (step === 1) {
    return (
      <Wrap title="技术选型 · 每层职责与选型理由" color={color} icon="⚙️">
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 10 }}>
          {[
            { icon: '🎨', t: '前端门户', d: 'React 19 + Ant Design', r: 'SPA + BFF 分工：SPA 只管 UI，认证逻辑在后端', c: '#3b82f6' },
            { icon: '🐍', t: '认证中心', d: 'Python FastAPI', r: '标准 OIDC Provider：authorize/token/userinfo/JWKS', c: '#10b981' },
            { icon: '📜', t: '认证协议', d: 'OAuth 2.1 + PKCE + OIDC', r: 'OAuth2.0 收敛强化版：强制 PKCE、明确 Token 职责', c: '#8b5cf6' },
            { icon: '🌐', t: '统一网关', d: 'Traefik forwardAuth', r: '统一 JWT 验签 + 注入身份，配置即接入', c: '#f59e0b' },
            { icon: '🗄️', t: '数据存储', d: 'PostgreSQL 外部共享库', r: '用户/应用/auth_codes/refresh_tokens/日志，独立容器', c: '#ef4444' },
            { icon: '🐳', t: '部署编排', d: 'Docker Compose', r: '一键全栈启动 · OrbStack 域名自动解析', c: '#0ea5e9' },
          ].map((item, i) => (
            <div key={i} style={{ background: '#fff', border: `1px solid ${item.c}30`, borderRadius: 10, padding: '12px 14px', boxShadow: '0 2px 8px rgba(0,0,0,.04)' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 6 }}>
                <span style={{ fontSize: 20 }}>{item.icon}</span>
                <span style={{ fontSize: 13, fontWeight: 700, color: '#1e293b' }}>{item.t}</span>
                <span style={{ marginLeft: 'auto', fontSize: 10, color: item.c, fontWeight: 700, background: `${item.c}12`, padding: '2px 8px', borderRadius: 4 }}>{item.d}</span>
              </div>
              <div style={{ fontSize: 11, color: '#64748b', lineHeight: 1.6 }}>{item.r}</div>
            </div>
          ))}
        </div>
      </Wrap>
    )
  }

  if (step === 2) {
    // OIDC 授权码 + PKCE 数据流时序图
    return (
      <Wrap title="关键数据流 · OIDC 授权码 + PKCE 全链路" color={color} icon="🔄">
        <svg viewBox="0 0 680 360" style={{ width: '100%', height: '100%' }}>
          <defs>
            <filter id="shadow2" x="-10%" y="-10%" width="120%" height="120%">
              <feDropShadow dx="0" dy="2" stdDeviation="2" floodOpacity="0.1" />
            </filter>
          </defs>
          {[
            { x: 60, name: '用户', tech: '浏览器' },
            { x: 200, name: '门户 SPA', tech: 'React' },
            { x: 340, name: '门户 BFF', tech: 'OIDC 客户端' },
            { x: 480, name: '认证中心', tech: 'OIDC Provider' },
            { x: 600, name: '业务系统', tech: '网关/直连/OIDC' },
          ].map((p, i) => (
            <g key={i}>
              <rect x={p.x - 40} y={10} width={80} height={36} rx={6} fill={color} filter="url(#shadow2)" />
              <text x={p.x} y={26} fontSize={11} fontWeight={700} fill="#fff" textAnchor="middle">{p.name}</text>
              <text x={p.x} y={38} fontSize={8} fill="#e2e8f0" textAnchor="middle">{p.tech}</text>
              <line x1={p.x} y1={50} x2={p.x} y2={340} stroke="#cbd5e1" strokeWidth={1} strokeDasharray="4 3" />
            </g>
          ))}
          <Arrow x1={60} y1={65} x2={200} y2={65} label="点击登录" color={color} />
          <Arrow x1={200} y1={92} x2={340} y2={92} label="发起登录(SPA 无凭证)" color={color} />
          <Arrow x1={340} y1={122} x2={480} y2={122} label="GET /authorize?client_id&PKCE" color="#3b82f6" />
          <Arrow x1={480} y1={150} x2={60} y2={150} label="302 到登录页" color="#f59e0b" />
          <Arrow x1={60} y1={180} x2={480} y2={180} label="输入账密提交" color={color} />
          <Arrow x1={480} y1={210} x2={340} y2={210} label="302 回一次性 code" color="#10b981" />
          <Arrow x1={340} y1={240} x2={480} y2={240} label="code+verifier+secret 换 token" color="#3b82f6" />
          <Arrow x1={480} y1={268} x2={340} y2={268} label="id/access/refresh token" color="#10b981" dashed />
          <Arrow x1={340} y1={295} x2={200} y2={295} label="建立 HttpOnly 会话" color={color} />
          <Arrow x1={200} y1={322} x2={60} y2={322} label="SPA 无感恢复用户" color="#8b5cf6" />
          <text x={340} y={352} fontSize={9.5} fill="#64748b" textAnchor="middle">Token 不进浏览器 · client_secret 只在 BFF · 业务系统另走网关/直连/OIDC</text>
        </svg>
      </Wrap>
    )
  }

  if (step === 3) {
    return (
      <Wrap title="部署与演进 · 已完成 vs 演进方向" color={color} icon="🚀">
        <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
          <div style={{ background: '#fff', borderRadius: 10, padding: '12px 16px', border: '1px solid #e2e8f0' }}>
            <div style={{ fontSize: 12, fontWeight: 700, color: '#166534', marginBottom: 8 }}>✅ 已完成：Docker Compose 一键编排（7 容器 + 外部共享库）</div>
            <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap' }}>
              {['认证中心(OIDC Provider)', '门户(React+BFF)', '网关(Traefik)', 'oidc-demo', 'mock-app', 'direct-app', 'pilot-app', 'devops-postgres(外部)'].map((c, i) => (
                <span key={i} style={{ background: '#f0fdf4', border: '1px solid #86efac', borderRadius: 6, padding: '4px 10px', fontSize: 10, color: '#14532d', fontWeight: 500 }}>{c}</span>
              ))}
            </div>
            <div style={{ fontSize: 11, color: '#475569', marginTop: 8, lineHeight: 1.7 }}>
              ✓ 标准 OIDC（PKCE / id_token / access_token） · ✓ refresh 轮换 + 复用检测 · ✓ 授权码哈希入库 · ✓ PostgreSQL 迁移
            </div>
          </div>
          <div style={{ textAlign: 'center', color, fontSize: 14, fontWeight: 700 }}>↓ 演进方向 ↓</div>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 8 }}>
            {[
              { t: 'JWKS 密钥轮换', d: 'kid 标识多公钥共存·新旧平滑过渡·旧 token 自然过期后下线', icon: '🔄' },
              { t: '启用真实 IdP', d: 'LDAP / Okta 可插拔身份源，配置启用并按序降级', icon: '🔌' },
              { t: 'BFF 独立部署', d: '门户 BFF 与 IdP 拆成独立服务（生产建议用现成 OIDC 库）', icon: '🧩' },
              { t: '真实系统接入', d: '按 OIDC 客户端 / 网关方式接入真实业务系统', icon: '📦' },
            ].map((item, i) => (
              <div key={i} style={{ background: '#fff', border: '1px dashed #cbd5e1', borderRadius: 8, padding: '10px 12px' }}>
                <div style={{ fontSize: 12, fontWeight: 700, color: '#1e293b' }}>{item.icon} {item.t}</div>
                <div style={{ fontSize: 10, color: '#64748b', marginTop: 4, lineHeight: 1.5 }}>{item.d}</div>
              </div>
            ))}
          </div>
        </div>
      </Wrap>
    )
  }

  // step 0: 四层架构
  return (
    <Wrap title="四层分层架构 · 职责解耦" color={color} icon="🏗️">
      <svg viewBox="0 0 680 440" style={{ width: '100%', height: '100%' }}>
        {SHADOW}
        {/* 接入层 */}
        <LayerBox x={20} y={20} w={640} h={80} label="接入层 · 统一入口与鉴权" color="#3b82f6" />
        <Box x={50} y={42} w={180} h={48} title="统一门户" tech="SPA + BFF（OIDC 客户端）" color="#3b82f6" />
        <Box x={260} y={42} w={180} h={48} title="统一网关" tech="Traefik · forwardAuth" color="#3b82f6" />
        <Box x={470} y={42} w={170} h={48} title="受保护业务API" tech="经网关统一拦截鉴权" color="#3b82f6" />

        {/* 认证层 */}
        <LayerBox x={20} y={122} w={640} h={90} label="认证层 · OIDC Provider" color="#10b981" />
        <Box x={50} y={144} w={140} h={56} title="授权端点" tech="authorize + PKCE" color="#10b981" />
        <Box x={210} y={144} w={140} h={56} title="令牌端点" tech="code 换 token" color="#10b981" />
        <Box x={370} y={144} w={140} h={56} title="用户信息/JWKS" tech="userinfo · JWKS" color="#10b981" />
        <Box x={530} y={144} w={110} h={56} title="应用注册" tech="client_id/secret" color="#10b981" />

        {/* 数据层 */}
        <LayerBox x={20} y={238} w={640} h={76} label="数据层 · PostgreSQL 外部共享库" color="#8b5cf6" />
        <Box x={60} y={260} w={140} h={44} title="用户表" tech="用户·角色·bcrypt密码" color="#8b5cf6" />
        <Box x={220} y={260} w={140} h={44} title="应用注册表" tech="元数据·凭证·回调白名单" color="#8b5cf6" />
        <Box x={380} y={260} w={140} h={44} title="授权码/刷新令牌" tech="auth_codes · refresh" color="#8b5cf6" />
        <Box x={540} y={260} w={90} h={44} title="认证日志" tech="审计" color="#8b5cf6" />

        {/* 身份源层 */}
        <LayerBox x={20} y={340} w={640} h={72} label="身份源层 · 可插拔用户来源" color="#ef4444" />
        <Box x={120} y={362} w={130} h={40} title="Local 本地库" tech="默认启用 · bcrypt" color="#ef4444" />
        <Box x={285} y={362} w={130} h={40} title="LDAP 目录服务" tech="可选 profile" color="#ef4444" active={false} />
        <Box x={450} y={362} w={130} h={40} title="Okta 企业IdP" tech="可插拔 · OIDC" color="#ef4444" active={false} />

        <Arrow x1={340} y1={100} x2={340} y2={122} color="#94a3b8" />
        <Arrow x1={340} y1={212} x2={340} y2={238} color="#94a3b8" />
        <Arrow x1={340} y1={314} x2={340} y2={340} color="#94a3b8" />
      </svg>
    </Wrap>
  )
}

/* ============ 场景3：统一认证 ============ */

export function AuthVisual({ step, color }: { step: number; color: string }) {
  if (step === 1) {
    // Token 体系：id / access / refresh
    return (
      <Wrap title="Token 体系 · 三权分离 + refresh 轮换" color={color} icon="🎫">
        <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit,minmax(160px,1fr))', gap: 10 }}>
            {[
              { t: 'id_token（身份断言）', d: 'JWT 签名，含 sub/nonce/aud\n证明"你是谁"，不用于调 API', c: '#3b82f6', icon: '🪪' },
              { t: 'access_token（访问凭证）', d: 'RS256 签名，短时效(1h)\n调 /userinfo 或业务 API', c: '#10b981', icon: '🎟️' },
              { t: 'refresh_token（续期凭证）', d: '长时效(7d)，仅后端持有\n换新 access_token', c: '#f59e0b', icon: '🔁' },
            ].map((i) => (
              <div key={i.t} style={{ background: '#fff', border: `1px solid ${i.c}35`, borderTop: `3px solid ${i.c}`, borderRadius: 10, padding: '12px 14px' }}>
                <div style={{ fontSize: 18 }}>{i.icon}</div>
                <div style={{ fontSize: 12.5, fontWeight: 700, color: '#1e293b', margin: '4px 0 4px' }}>{i.t}</div>
                <div style={{ fontSize: 10.5, color: '#64748b', lineHeight: 1.7, whiteSpace: 'pre-line' }}>{i.d}</div>
              </div>
            ))}
          </div>
          <div style={{ background: '#fffbeb', border: '1px solid #fcd34d', borderRadius: 10, padding: '10px 14px' }}>
            <div style={{ fontSize: 12, fontWeight: 700, color: '#92400e', marginBottom: 4 }}>🔁 refresh_token 轮换 + 复用检测</div>
            <div style={{ fontSize: 11, color: '#78350f', lineHeight: 1.7 }}>
              每次用 refresh_token 换新 token：旧号立即作废、签发新号（轮换）；若检测到旧号被再次使用，判定被窃取，<b>吊销整族会话</b>（复用检测）。
              本系统 refresh_token 以哈希形式入库，数据库泄露也无法直接使用。
            </div>
          </div>
        </div>
      </Wrap>
    )
  }

  if (step === 2) {
    // 身份源：Local 默认 + 降级链
    return (
      <Wrap title="身份源 · Local 默认，可插拔降级" color={color} icon="🔗">
        <svg viewBox="0 0 680 360" style={{ width: '100%', height: '100%' }}>
          {SHADOW}
          <Box x={270} y={15} w={140} h={45} title="用户登录请求" tech="用户名 + 密码" color={color} />
          <Box x={60} y={95} w={170} h={62} title="① Local 本地库" tech="bcrypt 密码校验" desc="默认启用" color="#10b981" />
          <Box x={270} y={95} w={170} h={62} title="② LDAP（可选）" tech="DN 搜索 + bind" desc="未启用 · 配置开启" color="#f59e0b" active={false} />
          <Box x={480} y={95} w={170} h={62} title="③ Okta（可选）" tech="OIDC 授权码" desc="未启用 · 配置开启" color="#ef4444" active={false} />
          <Arrow x1={340} y1={60} x2={145} y2={95} color={color} />
          <Arrow x1={230} y1={126} x2={270} y2={126} label="不可用则降级" color="#f59e0b" dashed />
          <Arrow x1={440} y1={126} x2={480} y2={126} label="不可用则降级" color="#f59e0b" dashed />
          <Box x={270} y={200} w={140} h={45} title="校验通过" tech="标准化 UserProfile" color="#10b981" />
          <Arrow x1={340} y1={157} x2={340} y2={200} label="任一通过" color="#10b981" />
          <Box x={270} y={270} w={140} h={45} title="签发 Token" tech="OIDC 授权码 + PKCE" color={color} />
          <Arrow x1={340} y1={245} x2={340} y2={270} color={color} />
          <rect x={30} y={318} width={290} height={38} rx={8} fill="#fef2f2" stroke="#ef4444" strokeWidth={1.5} />
          <text x={45} y={335} fontSize={11} fontWeight={700} fill="#991b1b">❌ 认证失败 → 直接 401，不降级</text>
          <text x={45} y={350} fontSize={9} fill="#7f1d1d">用户不存在/密码错误 = 明确失败，防止穿透弱身份源</text>
          <rect x={360} y={318} width={290} height={38} rx={8} fill="#f0fdf4" stroke="#22c55e" strokeWidth={1.5} />
          <text x={375} y={335} fontSize={11} fontWeight={700} fill="#166534">✅ 身份源不可用 → 降级下一个</text>
          <text x={375} y={350} fontSize={9} fill="#14532d">当前 Docker 环境：AUTH_PROVIDER_ORDER=local（仅本地库）</text>
        </svg>
      </Wrap>
    )
  }

  // step 0: OIDC 授权码 + PKCE 登录流程
  const steps = [
    { t: 'SPA 跳转', d: '门户 BFF 生成 PKCE 挑战值 + state + nonce', c: color },
    { t: '/authorize', d: '带 client_id、redirect_uri、PKCE challenge 跳认证中心', c: color },
    { t: '登录确认', d: '认证中心校验身份，授权页确认', c: color },
    { t: '回一次性 code', d: '302 带 code + state 回调（5 分钟有效）', c: color },
    { t: '换 token', d: 'BFF 用 code + code_verifier + client_secret 调 /token', c: color },
    { t: '校验 nonce', d: '验 id_token 的 nonce 防重放，建立会话', c: color },
  ]
  return (
    <Wrap title="OIDC 授权码 + PKCE 登录 · 六步标准流程" color={color} icon="🔐">
      <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
        {steps.map((s, i) => (
          <div key={i} style={{ display: 'flex', gap: 10, alignItems: 'flex-start', background: i === 2 ? '#fffbeb' : i === 3 ? '#f0fdf4' : '#fff', border: `1px solid ${s.c}30`, borderRadius: 10, padding: '8px 12px' }}>
            <span style={{ width: 22, height: 22, borderRadius: 6, background: color, color: '#fff', fontSize: 11, fontWeight: 700, display: 'flex', alignItems: 'center', justifyContent: 'center', flex: 'none', marginTop: 1 }}>{i + 1}</span>
            <div style={{ flex: 1 }}>
              <div style={{ fontSize: 12, fontWeight: 700, color: '#1e293b' }}>{s.t}</div>
              <div style={{ fontSize: 10.5, color: '#64748b', marginTop: 2 }}>{s.d}</div>
            </div>
          </div>
        ))}
        <div style={{ background: `${color}0d`, border: `1px solid ${color}30`, borderRadius: 10, padding: '10px 14px', fontSize: 11, color: '#475569', lineHeight: 1.7 }}>
          💡 <b>为什么 PKCE？</b> 即使授权码在回跳中被截获，攻击者没有 code_verifier 也换不到 token——把"授权码可换 token"绑定到申请方，是 OAuth 2.1 强制项。
        </div>
      </div>
    </Wrap>
  )
}

/* ============ 场景4：SSO与三种接入 ============ */

export function SSOVisual({ step, color }: { step: number; color: string }) {
  if (step === 0) {
    // SSO：BFF 会话 + 应用广场 sso-url
    return (
      <Wrap title="SSO 单点登录 · BFF 会话 + 应用广场统一 JWT" color={color} icon="🔄">
        <svg viewBox="0 0 680 340" style={{ width: '100%', height: '100%' }}>
          <defs>
            <filter id="shadow3" x="-10%" y="-10%" width="120%" height="120%">
              <feDropShadow dx="0" dy="2" stdDeviation="2" floodOpacity="0.1" />
            </filter>
          </defs>
          {[
            { x: 80, name: '用户', tech: '浏览器' },
            { x: 220, name: '门户 SPA', tech: 'React' },
            { x: 360, name: '门户 BFF', tech: 'OIDC 客户端' },
            { x: 500, name: '认证中心', tech: 'OIDC Provider' },
            { x: 620, name: '业务系统', tech: '应用广场跳转' },
          ].map((p, i) => (
            <g key={i}>
              <rect x={p.x - 38} y={10} width={76} height={32} rx={6} fill={color} filter="url(#shadow3)" />
              <text x={p.x} y={24} fontSize={10} fontWeight={700} fill="#fff" textAnchor="middle">{p.name}</text>
              <text x={p.x} y={35} fontSize={7.5} fill="#e2e8f0" textAnchor="middle">{p.tech}</text>
              <line x1={p.x} y1={48} x2={p.x} y2={320} stroke="#cbd5e1" strokeWidth={1} strokeDasharray="4 3" />
            </g>
          ))}
          <Arrow x1={80} y1={65} x2={220} y2={65} label="访问门户" color={color} />
          <Arrow x1={220} y1={92} x2={360} y2={92} label="发起 OIDC 登录" color={color} />
          <Arrow x1={360} y1={122} x2={500} y2={122} label="/authorize + PKCE" color="#3b82f6" />
          <Arrow x1={500} y1={150} x2={80} y2={150} label="登录页 / 输入账密" color="#f59e0b" />
          <Arrow x1={500} y1={180} x2={360} y2={180} label="一次性 code" color="#10b981" />
          <Arrow x1={360} y1={210} x2={500} y2={210} label="code+verifier+secret 换 token" color="#3b82f6" />
          <Arrow x1={360} y1={238} x2={220} y2={238} label="HttpOnly 会话" color={color} />
          <Arrow x1={220} y1={266} x2={80} y2={266} label="SPA 无感恢复用户" color="#8b5cf6" />
          <Arrow x1={220} y1={294} x2={620} y2={294} label="点击应用 → sso-url?token=统一JWT" color="#ef4444" />
          <text x={340} y={316} fontSize={9.5} fill="#64748b" textAnchor="middle">门户登录走标准 OIDC；应用广场跳转用统一 JWT（内部链路，Demo 模拟）</text>
        </svg>
      </Wrap>
    )
  }

  // 三种接入方式详细对比（step 1/2/3 高亮对应）
  const methods = [
    {
      idx: 1,
      icon: '🛡️',
      name: '方式一：经统一网关 forwardAuth',
      color: '#10b981',
      steps: [
        { from: '用户', to: '网关', label: '请求+Bearer 统一JWT' },
        { from: '网关', to: '认证中心', label: 'forwardAuth 转发验签' },
        { from: '认证中心', to: '网关', label: '200+用户信息' },
        { from: '网关', to: '业务后端', label: '注入 X-Auth-* 头转发' },
        { from: '业务后端', to: '用户', label: '返回数据（零鉴权代码）' },
      ],
      pros: ['业务系统零鉴权代码', '统一管控·审计·限流', '适合网关覆盖的内部应用'],
      cons: ['依赖网关可用性', '多一次内部 HTTP 调用'],
    },
    {
      idx: 2,
      icon: '🔗',
      name: '方式二：直连 JWKS 本地自验签',
      color: '#8b5cf6',
      steps: [
        { from: '用户', to: '业务服务', label: '请求+Bearer 统一JWT' },
        { from: '业务服务', to: '认证中心', label: '拉取 JWKS 公钥（缓存）' },
        { from: '业务服务', to: '业务服务', label: '本地 RS256 验签 + 过期检查' },
        { from: '业务服务', to: '用户', label: '通过则执行业务逻辑' },
      ],
      pros: ['不回源认证中心·高可用', '无网关依赖·适合外部部署', '性能好（本地验签）'],
      cons: ['每个服务需实现验签中间件', '公钥缓存需处理更新'],
    },
    {
      idx: 3,
      icon: '🎫',
      name: '方式三：OIDC 客户端接入（标准协议）',
      color: '#f59e0b',
      steps: [
        { from: '用户', to: '认证中心', label: 'GET /authorize?client_id&PKCE' },
        { from: '认证中心', to: '用户', label: '登录确认·返回一次性 code' },
        { from: '用户', to: '应用后端', label: '携带 code 回调（校验 state）' },
        { from: '应用后端', to: '认证中心', label: 'code+code_verifier+secret 换 token' },
        { from: '认证中心', to: '应用后端', label: 'access_token + id_token' },
        { from: '应用后端', to: '认证中心', label: '/userinfo 获取用户信息' },
      ],
      pros: ['最安全·token 不进浏览器', '标准协议·可对接任意 IdP', 'client_secret 仅后端持有'],
      cons: ['流程复杂·需后端配合', 'redirect_uri 需精确白名单'],
    },
  ]

  const active = methods[step - 1] || methods[0]
  return (
    <div style={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
      <SectionTitle icon={active.icon} text={active.name} color={active.color} />
      <div style={{ flex: 1, display: 'flex', flexDirection: 'column', gap: 8, overflow: 'auto' }}>
        <div style={{ background: '#fff', borderRadius: 10, padding: '10px 14px', border: `1px solid ${active.color}30` }}>
          <div style={{ fontSize: 11, fontWeight: 700, color: '#475569', marginBottom: 8 }}>📋 完整流程</div>
          {active.steps.map((s, i) => (
            <div key={i} style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 4 }}>
              <span style={{ width: 18, height: 18, borderRadius: 4, background: active.color, color: '#fff', fontSize: 10, fontWeight: 700, display: 'flex', alignItems: 'center', justifyContent: 'center', flex: 'none' }}>{i + 1}</span>
              <span style={{ fontSize: 11, color: '#334155', fontWeight: 600 }}>{s.from}</span>
              <span style={{ fontSize: 10, color: active.color, flex: 1, textAlign: 'center', borderBottom: `1px dashed ${active.color}40`, paddingBottom: 2 }}>{s.label} →</span>
              <span style={{ fontSize: 11, color: '#334155', fontWeight: 600 }}>{s.to}</span>
            </div>
          ))}
        </div>
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 8 }}>
          <div style={{ background: '#f0fdf4', border: '1px solid #86efac', borderRadius: 8, padding: '8px 10px' }}>
            <div style={{ fontSize: 11, fontWeight: 700, color: '#166534', marginBottom: 4 }}>✅ 优势</div>
            {active.pros.map((p, i) => (
              <div key={i} style={{ fontSize: 10, color: '#14532d', lineHeight: 1.6 }}>• {p}</div>
            ))}
          </div>
          <div style={{ background: '#fef2f2', border: '1px solid #fca5a5', borderRadius: 8, padding: '8px 10px' }}>
            <div style={{ fontSize: 11, fontWeight: 700, color: '#991b1b', marginBottom: 4 }}>⚠️ 局限</div>
            {active.cons.map((c, i) => (
              <div key={i} style={{ fontSize: 10, color: '#7f1d1d', lineHeight: 1.6 }}>• {c}</div>
            ))}
          </div>
        </div>
        {step === 3 && (
          <div style={{ background: `${active.color}0d`, border: `1px solid ${active.color}40`, borderRadius: 8, padding: '8px 12px', fontSize: 11, color: '#475569' }}>
            💡 门户本身就是方式三的实例：SPA 经门户 BFF（OIDC 客户端）走授权码 + PKCE 登录；oidc-demo 是独立的标准 OIDC 客户端演示。
          </div>
        )}
      </div>
    </div>
  )
}

/* ============ 场景5：应用生命周期 ============ */

export function LifecycleVisual({ step, color }: { step: number; color: string }) {
  if (step === 1) {
    // 两层身份模型 + OIDC 客户端配置
    return (
      <Wrap title="两层身份模型 + OIDC 客户端配置" color={color} icon="🔑">
        <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 10 }}>
            <div style={{ background: '#eff6ff', border: '2px solid #3b82f6', borderRadius: 12, padding: '14px' }}>
              <div style={{ fontSize: 14, fontWeight: 700, color: '#1e40af', marginBottom: 8 }}>👤 用户凭证（User Identity）</div>
              <div style={{ background: '#fff', borderRadius: 8, padding: '8px 10px', marginBottom: 8 }}>
                <div style={{ fontSize: 11, fontWeight: 700, color: '#1e3a8a' }}>id_token / access_token</div>
                <div style={{ fontSize: 9, color: '#64748b', marginTop: 2 }}>OIDC 登录签发，RS256 签名</div>
              </div>
              <div style={{ fontSize: 10, color: '#1e3a8a', lineHeight: 1.8 }}>
                • 证明「是哪个用户」<br />
                • id_token 含 sub/nonce/aud<br />
                • 业务系统验签或用 userinfo<br />
                • access_token 短时效，refresh 续期
              </div>
            </div>
            <div style={{ background: '#f0fdf4', border: '2px solid #22c55e', borderRadius: 12, padding: '14px' }}>
              <div style={{ fontSize: 14, fontWeight: 700, color: '#166534', marginBottom: 8 }}>📱 应用凭证（App Identity）</div>
              <div style={{ background: '#fff', borderRadius: 8, padding: '8px 10px', marginBottom: 8 }}>
                <div style={{ fontSize: 11, fontWeight: 700, color: '#14532d' }}>client_id + client_secret</div>
                <div style={{ fontSize: 9, color: '#64748b', marginTop: 2 }}>注册时自动发放，secret 仅展示一次</div>
              </div>
              <div style={{ fontSize: 10, color: '#14532d', lineHeight: 1.8 }}>
                • 证明「是哪个应用」<br />
                • client_id = 公开标识<br />
                • client_secret = 机密（仅后端）<br />
                • OIDC 流程中用于换 token
              </div>
            </div>
          </div>
          <div style={{ background: `${color}0d`, border: `1px solid ${color}30`, borderRadius: 10, padding: '12px 16px' }}>
            <div style={{ fontSize: 12, fontWeight: 700, color: '#1e293b', marginBottom: 6 }}>🔗 OIDC 客户端的三个关键配置</div>
            <div style={{ fontSize: 11, color: '#475569', lineHeight: 1.9 }}>
              ① <b>redirect_uri 白名单</b>：精确匹配回调地址，防回调劫持；② <b>PKCE</b>：强制 code_verifier，防授权码拦截；③ <b>client_secret</b>：仅应用后端持有，换取 token 的凭证。
            </div>
          </div>
        </div>
      </Wrap>
    )
  }

  // step 0: 应用注册流程
  return (
    <Wrap title="应用注册与上架全流程" color={color} icon="📋">
      <svg viewBox="0 0 680 330" style={{ width: '100%', height: '100%' }}>
        <defs>
          <filter id="shadow5" x="-10%" y="-10%" width="120%" height="120%">
            <feDropShadow dx="0" dy="2" stdDeviation="3" floodOpacity="0.1" />
          </filter>
        </defs>
        {[
          { x: 20, icon: '📝', t: '填写基本信息', d: '名称·图标·描述' },
          { x: 155, icon: '🔗', t: 'OIDC 配置', d: 'redirect_uri 白名单·PKCE' },
          { x: 290, icon: '🔑', t: '自动发放凭证', d: 'client_id + client_secret' },
          { x: 425, icon: '📄', t: '接入说明', d: '三种接入方式配置' },
          { x: 560, icon: '🚀', t: '上架 + SSO 进入', d: '数据驱动·无需重启' },
        ].map((item, i) => (
          <g key={i}>
            <rect x={item.x} y={40} width={100} height={92} rx={10} fill="#fff" stroke={color} strokeWidth={1.5} filter="url(#shadow5)" />
            <rect x={item.x} y={40} width={100} height={6} rx={3} fill={color} />
            <text x={item.x + 50} y={72} fontSize={22} textAnchor="middle">{item.icon}</text>
            <text x={item.x + 50} y={95} fontSize={11} fontWeight={700} fill="#1e293b" textAnchor="middle">{item.t}</text>
            <text x={item.x + 50} y={115} fontSize={8.5} fill="#64748b" textAnchor="middle">{item.d}</text>
            {i < 4 && (
              <g>
                <line x1={item.x + 100} y1={86} x2={item.x + 155} y2={86} stroke={color} strokeWidth={2} markerEnd={`url(#arrow-main)`} />
                <defs><marker id="arrow-main" markerWidth="8" markerHeight="6" refX="7" refY="3" orient="auto"><polygon points="0 0, 8 3, 0 6" fill={color} /></marker></defs>
              </g>
            )}
          </g>
        ))}
        <rect x={20} y={160} width={640} height={58} rx={10} fill={`${color}08`} stroke={`${color}30`} />
        <text x={40} y={182} fontSize={12} fontWeight={700} fill="#1e293b">🎛️ 开发者控制台（门户内置）</text>
        <text x={40} y={202} fontSize={10} fill="#475569">• 向导式注册：基本信息 → OIDC 配置 → 凭证发放 → 接入说明 → 上架</text>
        <rect x={20} y={232} width={640} height={58} rx={10} fill="#f0fdf4" stroke="#86efac" />
        <text x={40} y={254} fontSize={12} fontWeight={700} fill="#166534">💡 核心设计：数据驱动的应用注册表</text>
        <text x={40} y={274} fontSize={10} fill="#14532d">• 应用信息存数据库，门户读取即上架，无需重启 · 支持上下架、接入方式配置、回调白名单管理</text>
        <text x={40} y={288} fontSize={10} fill="#14532d">• client_secret 仅发放时展示一次，支持重置（安全设计）</text>
      </svg>
    </Wrap>
  )
}

/* ============ 场景6：安全设计 ============ */

export function SecurityVisual({ step, color }: { step: number; color: string }) {
  if (step === 1) {
    // Token 安全 + 凭证传递
    return (
      <Wrap title="Token 安全 · 轮换 + 复用检测 + 凭证传递" color={color} icon="🔐">
        <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 10 }}>
            <div style={{ background: '#f0fdf4', border: '1px solid #86efac', borderRadius: 10, padding: '12px 14px' }}>
              <div style={{ fontSize: 12.5, fontWeight: 700, color: '#166534', marginBottom: 4 }}>🔁 refresh_token 轮换</div>
              <div style={{ fontSize: 11, color: '#14532d', lineHeight: 1.7 }}>
                每次使用即作废旧号、签发新号。旧号无法再用——即使泄漏，攻击者拿到的旧号也无效。
              </div>
            </div>
            <div style={{ background: '#fef2f2', border: '1px solid #fca5a5', borderRadius: 10, padding: '12px 14px' }}>
              <div style={{ fontSize: 12.5, fontWeight: 700, color: '#991b1b', marginBottom: 4 }}>🚨 复用检测</div>
              <div style={{ fontSize: 11, color: '#7f1d1d', lineHeight: 1.7 }}>
                检测到旧号被再次使用 → 判定整族会话被窃取，立即吊销该用户全部 refresh_token。
              </div>
            </div>
          </div>
          {[
            { way: 'OIDC 授权码 + PKCE', level: '最安全', levelColor: '#3b82f6', icon: '🏆', d: 'Token 永远不进浏览器。前端只拿一次性 code，后端用 code+verifier+secret 换 token。即使 code 被截获也无法单独使用。', risk: '极低' },
            { way: 'HttpOnly Cookie（门户 BFF 会话）', level: '推荐', levelColor: '#10b981', icon: '✅', d: 'Cookie 设置 HttpOnly，JS 无法读取，防 XSS 窃取。门户 SPA 会话即此方式。', risk: '低' },
            { way: 'Authorization: Bearer <token>', level: '推荐', levelColor: '#10b981', icon: '✅', d: 'RFC 6750 标准方式。Token 在 Header 传递，不暴露在 URL / 历史 / 日志。配合 HTTPS。', risk: '低' },
            { way: 'URL 参数 (?token=xxx)', level: '内部链路 Demo', levelColor: '#f59e0b', icon: '⚠️', d: '用于应用广场 SSO 跳转瞬间传递统一 JWT。生产应替换为 Cookie 或 OIDC。', risk: '中' },
          ].map((item, i) => (
            <div key={i} style={{ background: '#fff', border: `1px solid ${item.levelColor}30`, borderRadius: 10, padding: '10px 14px', display: 'flex', gap: 10, alignItems: 'flex-start' }}>
              <span style={{ fontSize: 18, flex: 'none' }}>{item.icon}</span>
              <div style={{ flex: 1 }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 4 }}>
                  <span style={{ fontSize: 12, fontWeight: 700, color: '#1e293b', fontFamily: 'monospace' }}>{item.way}</span>
                  <span style={{ fontSize: 9, color: '#fff', background: item.levelColor, padding: '2px 8px', borderRadius: 4, fontWeight: 700 }}>{item.level}</span>
                  <span style={{ fontSize: 9, color: '#64748b', marginLeft: 'auto' }}>风险: {item.risk}</span>
                </div>
                <div style={{ fontSize: 10, color: '#475569', lineHeight: 1.6 }}>{item.d}</div>
              </div>
            </div>
          ))}
        </div>
      </Wrap>
    )
  }

  if (step === 2) {
    // 身份与审计
    return (
      <Wrap title="身份与审计 · 认证失败不降级 + 全量审计" color={color} icon="🛡️">
        <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 10 }}>
            <div style={{ background: '#fef2f2', border: '1px solid #fca5a5', borderRadius: 10, padding: '12px 14px' }}>
              <div style={{ fontSize: 12.5, fontWeight: 700, color: '#991b1b', marginBottom: 4 }}>❌ 认证失败 → 直接 401</div>
              <div style={{ fontSize: 11, color: '#7f1d1d', lineHeight: 1.7 }}>
                用户不存在 / 密码错误是明确失败，绝不降级到弱身份源——防止攻击者穿透。
              </div>
            </div>
            <div style={{ background: '#f0fdf4', border: '1px solid #86efac', borderRadius: 10, padding: '12px 14px' }}>
              <div style={{ fontSize: 12.5, fontWeight: 700, color: '#166534', marginBottom: 4 }}>✅ 身份源不可用 → 降级</div>
              <div style={{ fontSize: 11, color: '#14532d', lineHeight: 1.7 }}>
                连接超时 / 服务宕机才触发降级链（当前默认仅 Local），保证登录不中断。
              </div>
            </div>
          </div>
          <div style={{ background: '#fffbeb', border: '1px solid #fcd34d', borderRadius: 10, padding: '12px 14px' }}>
            <div style={{ fontSize: 12.5, fontWeight: 700, color: '#92400e', marginBottom: 4 }}>📝 全量认证审计</div>
            <div style={{ fontSize: 11, color: '#78350f', lineHeight: 1.7 }}>
              每次登录的来源（local/ldap/okta）、结果（成功/失败）、IP、时间戳写入认证日志表。管理员通过「系统 → 认证日志」可审计。安全事件可追溯。
            </div>
          </div>
          <div style={{ background: `${color}0d`, border: `1px solid ${color}30`, borderRadius: 10, padding: '10px 14px', fontSize: 11, color: '#475569', lineHeight: 1.7 }}>
            💡 <b>协议层四重防护回顾：</b>state 防 CSRF · nonce 防重放 · PKCE 防授权码劫持 · 授权码一次性+哈希入库防数据库泄露。OIDC 标准把这些安全默认内置，而不是自己发明。
          </div>
        </div>
      </Wrap>
    )
  }

  // step 0: 协议级安全（state / nonce / PKCE / 一次性授权码）
  const items = [
    { icon: '🎯', t: 'state 防 CSRF', d: '发起时生成随机 state，回调时严格比对。攻击者无法伪造合法回调', c: '#3b82f6' },
    { icon: '🔢', t: 'nonce 防重放', d: 'id_token 内嵌 nonce，客户端校验一致，防止 token 重放攻击', c: '#10b981' },
    { icon: '🔐', t: 'PKCE 防拦截', d: 'code_verifier 只有申请方持有，截获授权码也换不到 token', c: '#8b5cf6' },
    { icon: '⏱️', t: '一次性授权码', d: '5 分钟有效、用过即废、哈希入库——数据库泄露也无法直接使用', c: '#f59e0b' },
  ]
  return (
    <Wrap title="协议级安全 · OIDC 四重内置防护" color={color} icon="🛡️">
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 10 }}>
        {items.map((i) => (
          <div key={i.t} style={{ background: '#fff', border: `1px solid ${i.c}35`, borderTop: `3px solid ${i.c}`, borderRadius: 10, padding: '14px' }}>
            <div style={{ fontSize: 20 }}>{i.icon}</div>
            <div style={{ fontSize: 13, fontWeight: 700, color: '#1e293b', margin: '6px 0 4px' }}>{i.t}</div>
            <div style={{ fontSize: 11, color: '#64748b', lineHeight: 1.7 }}>{i.d}</div>
          </div>
        ))}
      </div>
      <div style={{ marginTop: 10, background: `${color}0d`, border: `1px solid ${color}30`, borderRadius: 10, padding: '10px 14px', fontSize: 11, color: '#475569', lineHeight: 1.7 }}>
        💡 <b>核心思想：</b>安全不是自己发明，而是用标准协议内置的防护。这套防护在 OAuth 2.1 / OIDC 里是默认项，符合企业级安全基线。
      </div>
    </Wrap>
  )
}

/* ============ 目录页迷你缩略图 ============ */

export function SceneThumbnail({ sceneId, color }: { sceneId: string; color: string }) {
  const size = 52
  const common: React.CSSProperties = { width: size, height: size, borderRadius: 10, display: 'flex', alignItems: 'center', justifyContent: 'center', background: `${color}12`, border: `1px solid ${color}30` }

  switch (sceneId) {
    case 'overview':
      return (
        <div style={common}>
          <svg width="36" height="28" viewBox="0 0 36 28">
            <rect x="0" y="8" width="8" height="12" rx="2" fill={color} />
            <rect x="14" y="0" width="8" height="12" rx="2" fill={color} opacity="0.7" />
            <rect x="14" y="16" width="8" height="12" rx="2" fill={color} opacity="0.7" />
            <rect x="28" y="8" width="8" height="12" rx="2" fill={color} opacity="0.5" />
          </svg>
        </div>
      )
    case 'architecture':
      return (
        <div style={{ ...common, flexDirection: 'column', gap: 2 }}>
          {[0.9, 0.7, 0.5, 0.3].map((op, i) => (
            <div key={i} style={{ width: 32, height: 5, borderRadius: 2, background: color, opacity: op }} />
          ))}
        </div>
      )
    case 'auth':
      return (
        <div style={common}>
          <svg width="28" height="26" viewBox="0 0 28 26">
            <rect x="1" y="1" width="26" height="24" rx="4" fill="none" stroke={color} strokeWidth="1.5" />
            <path d="M9 8 L14 13 L19 8" stroke={color} strokeWidth="2" fill="none" strokeLinecap="round" strokeLinejoin="round" />
          </svg>
        </div>
      )
    case 'sso':
      return (
        <div style={common}>
          <div style={{ display: 'flex', gap: 3 }}>
            {['#10b981', '#8b5cf6', '#f59e0b'].map((c, i) => (
              <div key={i} style={{ width: 7, height: 26, borderRadius: 2, background: c }} />
            ))}
          </div>
        </div>
      )
    case 'lifecycle':
      return (
        <div style={common}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            {[0, 1, 2, 3].map((i) => (
              <React.Fragment key={i}>
                <div style={{ width: 7, height: 7, borderRadius: 3.5, background: color }} />
                {i < 3 && <span style={{ color, fontSize: 8, fontWeight: 700 }}>→</span>}
              </React.Fragment>
            ))}
          </div>
        </div>
      )
    case 'security':
      return (
        <div style={common}>
          <svg width="26" height="28" viewBox="0 0 24 26" fill="none">
            <path d="M12 2L3 6v8c0 5.5 3.8 9.5 9 10 5.2-.5 9-4.5 9-10V6l-9-4z" fill={`${color}20`} stroke={color} strokeWidth="1.5" />
            <path d="M8 13l2.5 2.5L16 9" stroke={color} strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
          </svg>
        </div>
      )
    default:
      return <div style={common}><span style={{ fontSize: 20 }}>📊</span></div>
  }
}

/* ============ 场景渲染映射 ============ */

export function renderSceneVisual(sceneId: string, step: number, color: string) {
  switch (sceneId) {
    case 'overview': return <OverviewVisual step={step} color={color} />
    case 'architecture': return <ArchitectureVisual step={step} color={color} />
    case 'auth': return <AuthVisual step={step} color={color} />
    case 'sso': return <SSOVisual step={step} color={color} />
    case 'lifecycle': return <LifecycleVisual step={step} color={color} />
    case 'security': return <SecurityVisual step={step} color={color} />
    default: return null
  }
}
