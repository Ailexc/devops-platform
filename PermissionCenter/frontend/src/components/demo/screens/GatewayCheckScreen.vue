<template>
  <div class="mock-screen">
    <div class="mock-topbar"><div class="mock-breadcrumb">网关鉴权</div><div class="mock-user">🌐 Traefik PEP</div></div>
    <div class="mock-content">
      <h2 class="mock-title">🌐 网关鉴权 — 实时生效</h2>
      <p class="mock-sub">Traefik forwardAuth → iam-server /v1/gateway/check → 实时决策</p>
      <div class="gw-card">
        <div class="gw-req"><code>GET /api/v1/hosts</code><span class="gw-user">X-User: bob</span></div>
        <div class="gw-steps">
          <div class="gw-step"><span class="gw-badge pep">PEP</span>请求转发 → 注入 X-PEP-Token</div>
          <div class="gw-step"><span class="gw-badge pdp">PDP</span>Casbin: bob ∈ 研发一部 → host:list ✓</div>
          <div class="gw-step"><span class="gw-badge pdp">PDP</span>OpenFGA: bob can_read → [host-01, host-02]</div>
        </div>
        <div class="gw-result ok"><strong>200 OK</strong> — 返回 bob 有权限的主机数据</div>
      </div>
      <div class="gw-card deny">
        <div class="gw-req"><code>POST /api/v1/hosts</code><span class="gw-user">X-User: bob</span></div>
        <div class="gw-steps">
          <div class="gw-step"><span class="gw-badge pep">PEP</span>请求转发 → 注入 X-PEP-Token</div>
          <div class="gw-step"><span class="gw-badge fail">DENY</span>Casbin: 无 host:create 权限</div>
        </div>
        <div class="gw-result deny"><strong>403 Forbidden</strong> — 写操作被拒绝</div>
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
.gw-card { background: var(--bg-card); border: 1px solid var(--border); border-radius: 10px; padding: 12px 14px; margin-bottom: 10px; }
.gw-card.deny { border-color: var(--danger); }
.gw-req { display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px; }
.gw-req code { font-family: var(--font-mono); font-size: 13px; font-weight: 600; color: var(--text); background: var(--bg-tertiary); padding: 4px 10px; border-radius: 4px; }
.gw-user { font-size: 11px; color: var(--text-tertiary); font-family: var(--font-mono); }
.gw-steps { display: flex; flex-direction: column; gap: 4px; margin-bottom: 10px; }
.gw-step { display: flex; align-items: center; gap: 8px; padding: 5px 10px; background: var(--bg-secondary); border-radius: 5px; font-size: 12px; color: var(--text); }
.gw-badge { font-size: 9px; font-weight: 700; padding: 1px 5px; border-radius: 3px; }
.gw-badge.pep { background: var(--info-bg); color: var(--info); }
.gw-badge.pdp { background: var(--success-bg); color: var(--success); }
.gw-badge.fail { background: var(--danger-bg); color: var(--danger); }
.gw-result { padding: 8px 12px; border-radius: 6px; font-size: 12px; font-weight: 600; }
.gw-result.ok { background: var(--success-bg); color: var(--success); }
.gw-result.deny { background: var(--danger-bg); color: var(--danger); }
</style>
