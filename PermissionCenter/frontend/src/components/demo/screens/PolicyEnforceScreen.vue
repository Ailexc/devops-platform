<template>
  <div class="mock-screen">
    <div class="mock-topbar"><div class="mock-breadcrumb">网关鉴权</div><div class="mock-user">🌐 Traefik PEP</div></div>
    <div class="mock-content">
      <h2 class="mock-title">🌐 策略执行 — 双引擎实时鉴权</h2>
      <p class="mock-sub">每个 API 请求经过 Casbin（动作级）+ OpenFGA（实例级）双重校验</p>

      <div class="enforce-card">
        <div class="ec-header"><code>GET /api/v1/hosts</code><span class="ec-user">X-User: bob</span></div>
        <div class="ec-steps">
          <div class="ec-step">
            <div class="ec-badge pep">PEP</div>
            <div class="ec-info">
              <div class="ec-title">请求解析</div>
              <div class="ec-desc">GET /api/v1/hosts → 映射为 action: <code>host:list</code></div>
            </div>
          </div>
          <div class="ec-step">
            <div class="ec-badge casbin">Casbin</div>
            <div class="ec-info">
              <div class="ec-title">动作级校验</div>
              <div class="ec-desc">p = user:bob, action:host:list → <strong class="ok">匹配 ✓</strong></div>
            </div>
          </div>
          <div class="ec-step">
            <div class="ec-badge fga">OpenFGA</div>
            <div class="ec-info">
              <div class="ec-title">实例级校验</div>
              <div class="ec-desc">ListObjects(user=bob, type=host) → <strong class="ok">[host-01, host-02]</strong></div>
            </div>
          </div>
        </div>
        <div class="ec-result ok"><strong>200 OK</strong> — 返回 bob 有权限的 2 台主机</div>
      </div>

      <div class="enforce-card deny">
        <div class="ec-header"><code>POST /api/v1/hosts</code><span class="ec-user">X-User: bob</span></div>
        <div class="ec-steps">
          <div class="ec-step"><div class="ec-badge pep">PEP</div><div class="ec-info"><div class="ec-title">请求解析</div><div class="ec-desc">POST /api/v1/hosts → 映射为 action: <code>host:create</code></div></div></div>
          <div class="ec-step"><div class="ec-badge casbin fail">Casbin</div><div class="ec-info"><div class="ec-title">动作级校验</div><div class="ec-desc">无 host:create 策略 → <strong class="fail">不匹配 ✗</strong></div></div></div>
        </div>
        <div class="ec-result deny"><strong>403 Forbidden</strong> — bob 无创建主机权限</div>
      </div>
    </div>
  </div>
</template>
<style scoped>
.mock-screen { width: 100%; flex: 1; min-height: 0; display: flex; flex-direction: column; background: var(--bg); }
.mock-topbar { display: flex; justify-content: space-between; align-items: center; padding: 12px 20px; background: var(--bg-card); border-bottom: 1px solid var(--border); font-size: 13px; color: var(--text-secondary); }
.mock-user { font-weight: 500; }
.mock-content { flex: 1; padding: 16px 22px; overflow: auto; }
.mock-title { font-size: 17px; font-weight: 700; color: var(--text); margin-bottom: 2px; }
.mock-sub { font-size: 11px; color: var(--text-secondary); margin-bottom: 12px; }
.enforce-card { background: var(--bg-card); border: 1px solid var(--border); border-radius: 10px; padding: 12px 14px; margin-bottom: 10px; }
.enforce-card.deny { border-color: var(--danger); }
.ec-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px; }
.ec-header code { font-family: var(--font-mono); font-size: 13px; font-weight: 600; background: var(--bg-tertiary); padding: 3px 8px; border-radius: 4px; }
.ec-user { font-size: 10px; color: var(--text-tertiary); font-family: var(--font-mono); }
.ec-steps { display: flex; flex-direction: column; gap: 6px; margin-bottom: 10px; }
.ec-step { display: flex; gap: 8px; align-items: flex-start; padding: 6px 8px; background: var(--bg-secondary); border-radius: 6px; }
.ec-badge { font-size: 9px; font-weight: 700; padding: 2px 6px; border-radius: 3px; flex-shrink: 0; margin-top: 1px; }
.ec-badge.pep { background: var(--info-bg); color: var(--info); }
.ec-badge.casbin { background: var(--success-bg); color: var(--success); }
.ec-badge.casbin.fail { background: var(--danger-bg); color: var(--danger); }
.ec-badge.fga { background: var(--purple-bg); color: var(--purple); }
.ec-title { font-size: 11px; font-weight: 600; color: var(--text); }
.ec-desc { font-size: 10px; color: var(--text-secondary); }
.ec-desc code { font-family: var(--font-mono); font-size: 10px; }
.ok { color: var(--success); }
.fail { color: var(--danger); }
.ec-result { padding: 6px 10px; border-radius: 6px; font-size: 12px; font-weight: 600; }
.ec-result.ok { background: var(--success-bg); color: var(--success); }
.ec-result.deny { background: var(--danger-bg); color: var(--danger); }
</style>
