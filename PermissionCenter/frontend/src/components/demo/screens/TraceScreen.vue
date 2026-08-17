<template>
  <div class="mock-screen">
    <div class="mock-topbar"><div class="mock-breadcrumb">系统观测 / <b>鉴权链路追踪</b></div><div class="mock-user">👤 admin</div></div>
    <div class="mock-content">
      <h2 class="mock-title">🔍 鉴权链路追踪</h2>
      <p class="mock-sub">每个网关请求生成 TraceID，完整记录 PEP→PDP 决策过程</p>
      <div class="trace-card">
        <div class="trace-header">
          <span class="trace-id">TraceID: a1b2c3d4</span>
          <span class="trace-time">2026-08-08 10:32:15</span>
        </div>
        <div class="trace-steps">
          <div class="t-step"><span class="t-badge pep">PEP</span><span class="t-desc">请求解析：GET /api/v1/hosts → host:list</span><span class="t-time">2ms</span></div>
          <div class="t-step"><span class="t-badge pdp">PDP</span><span class="t-desc">Casbin 策略匹配 → 组权限 host:list ✓</span><span class="t-time">1ms</span></div>
          <div class="t-step"><span class="t-badge pdp">PDP</span><span class="t-desc">OpenFGA Check → bob can_read host-01 → allow</span><span class="t-time">3ms</span></div>
          <div class="t-step ok"><span class="t-badge result">ALLOW</span><span class="t-desc">最终决策：200 OK</span><span class="t-time">6ms</span></div>
        </div>
      </div>
      <div class="trace-card deny">
        <div class="trace-header"><span class="trace-id">TraceID: e5f6g7h8</span><span class="trace-time">2026-08-08 10:32:18</span></div>
        <div class="trace-steps">
          <div class="t-step"><span class="t-badge pep">PEP</span><span class="t-desc">请求解析：POST /api/v1/hosts → host:create</span></div>
          <div class="t-step"><span class="t-badge pdp">PDP</span><span class="t-desc">Casbin 策略匹配 → 无 host:create 权限</span></div>
          <div class="t-step deny"><span class="t-badge result">DENY</span><span class="t-desc">最终决策：403 Forbidden</span></div>
        </div>
      </div>
    </div>
  </div>
</template>
<style scoped>
.mock-screen { width: 100%; flex: 1; min-height: 0; display: flex; flex-direction: column; background: var(--bg); }
.mock-topbar { display: flex; justify-content: space-between; align-items: center; padding: 12px 20px; background: var(--bg-card); border-bottom: 1px solid var(--border); font-size: 13px; color: var(--text-secondary); }
.mock-user { font-weight: 500; }
.mock-content { flex: 1; padding: 20px 24px; overflow: auto; }
.mock-title { font-size: 18px; font-weight: 700; color: var(--text); margin-bottom: 4px; }
.mock-sub { font-size: 12px; color: var(--text-secondary); margin-bottom: 14px; }
.trace-card { background: var(--bg-card); border: 1px solid var(--border); border-radius: 10px; padding: 14px; margin-bottom: 10px; }
.trace-card.deny { border-color: var(--danger); }
.trace-header { display: flex; justify-content: space-between; margin-bottom: 10px; }
.trace-id { font-family: var(--font-mono); font-size: 12px; font-weight: 600; color: var(--brand); }
.trace-time { font-size: 11px; color: var(--text-tertiary); }
.trace-steps { display: flex; flex-direction: column; gap: 4px; }
.t-step { display: flex; align-items: center; gap: 8px; padding: 6px 10px; background: var(--bg-secondary); border-radius: 6px; font-size: 12px; }
.t-step.ok { background: var(--success-bg); }
.t-step.deny { background: var(--danger-bg); }
.t-badge { font-size: 9px; font-weight: 700; padding: 2px 6px; border-radius: 3px; flex-shrink: 0; }
.t-badge.pep { background: var(--info-bg); color: var(--info); }
.t-badge.pdp { background: var(--success-bg); color: var(--success); }
.t-badge.result { background: var(--brand); color: #fff; }
.t-desc { flex: 1; color: var(--text); }
.t-time { font-size: 10px; color: var(--text-tertiary); font-family: var(--font-mono); }
</style>
