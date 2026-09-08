<template>
  <div class="mock-screen">
    <div class="mock-topbar"><div class="mock-breadcrumb">系统观测 / <b>PEP 解析工作台</b></div><div class="mock-user">👤 admin</div></div>
    <div class="mock-content">
      <h2 class="mock-title">⚙️ PEP 解析工作台</h2>
      <p class="mock-sub">网关请求 → action 映射 → 策略匹配，步骤化可视化</p>
      <div class="resolver-card">
        <div class="res-label">输入</div>
        <div class="res-input"><code>Method: GET &nbsp; URI: /api/v1/hosts &nbsp; X-User: bob</code></div>
        <div class="res-arrow">↓</div>
        <div class="res-label">Step 1: 字面匹配</div>
        <div class="res-step"><span class="step-match ok">✓</span><code>cmdb:host:list</code><span class="step-desc">精确命中</span></div>
        <div class="res-arrow">↓</div>
        <div class="res-label">Step 2: 策略评估</div>
        <div class="res-step"><span class="step-match ok">✓</span>Casbin 匹配：bob ∈ 研发一部 → host:list 有权限</div>
        <div class="res-arrow">↓</div>
        <div class="res-label">Step 3: 数据策略</div>
        <div class="res-step"><span class="step-match ok">✓</span>OpenFGA Check：bob can_read [host-01, host-02]</div>
        <div class="res-arrow">↓</div>
        <div class="res-result ok">ALLOW — 返回 host-01, host-02（数据范围过滤）</div>
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
.resolver-card { max-width: 45%; margin: 0 auto; }
.res-label { font-size: 10px; font-weight: 600; color: var(--text-tertiary); margin-bottom: 4px; text-transform: uppercase; letter-spacing: 0.05em; }
.res-input { background: #1e293b; border-radius: 6px; padding: 8px 12px; margin-bottom: 6px; }
.res-input code { font-family: var(--font-mono); font-size: 11px; color: #e2e8f0; }
.res-arrow { text-align: center; color: var(--brand); font-size: 14px; padding: 2px 0; }
.res-step { display: flex; align-items: center; gap: 8px; padding: 6px 10px; background: var(--bg-card); border: 1px solid var(--border); border-radius: 6px; font-size: 12px; color: var(--text); margin-bottom: 6px; }
.step-match { font-weight: 700; font-size: 12px; }
.step-match.ok { color: var(--success); }
.res-step code { font-family: var(--font-mono); font-size: 11px; }
.step-desc { margin-left: auto; font-size: 10px; color: var(--text-tertiary); }
.res-result { padding: 8px 12px; border-radius: 6px; font-size: 12px; font-weight: 600; }
.res-result.ok { background: var(--success-bg); color: var(--success); border: 1px solid var(--success); }
</style>
