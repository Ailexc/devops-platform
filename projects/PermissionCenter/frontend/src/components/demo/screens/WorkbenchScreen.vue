<template>
  <div class="mock-screen workbench-screen">
    <div class="mock-topbar">
      <div class="mock-breadcrumb">🏠 工作台</div>
      <div class="mock-user">👤 小黄</div>
    </div>
    <div class="mock-content">
      <h2 class="mock-title">工作台</h2>
      <div class="identity-card">
        <div class="id-avatar">黄</div>
        <div>
          <div class="id-name">小黄</div>
          <div class="id-sub">总公司 → 研发中心 → 监控服务应用 Owner</div>
        </div>
      </div>
      <div class="stats-row">
        <div class="stat-card"><div class="stat-val">3</div><div class="stat-label">组织权限</div></div>
        <div class="stat-card"><div class="stat-val">2</div><div class="stat-label">个人权限</div></div>
        <div class="stat-card highlight"><div class="stat-val">1</div><div class="stat-label">负责应用</div></div>
      </div>
      <h3 class="section-title">我的应用</h3>
      <div class="app-card active">
        <div class="app-icon">📡</div>
        <div class="app-info">
          <div class="app-name">小黄的监控服务</div>
          <div class="app-code">monitor</div>
        </div>
        <div class="app-badge">active</div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.mock-screen { width: 100%; flex: 1; min-height: 0; display: flex; flex-direction: column; background: var(--bg); }
.mock-topbar { display: flex; justify-content: space-between; align-items: center; padding: 12px 20px; background: var(--bg-card); border-bottom: 1px solid var(--border); font-size: 13px; color: var(--text-secondary); }
.mock-user { font-weight: 500; }
.mock-content { flex: 1; padding: 24px; overflow: auto; }
.mock-title { font-size: 20px; font-weight: 700; margin-bottom: 16px; color: var(--text); }
.identity-card { display: flex; align-items: center; gap: 14px; padding: 16px; background: var(--brand-soft); border: 1px solid var(--brand); border-radius: 10px; margin-bottom: 20px; }
.id-avatar { width: 44px; height: 44px; border-radius: 50%; background: var(--brand); color: #fff; display: flex; align-items: center; justify-content: center; font-weight: 700; font-size: 18px; }
.id-name { font-size: 16px; font-weight: 600; color: var(--text); }
.id-sub { font-size: 12px; color: var(--text-secondary); margin-top: 2px; }
.stats-row { display: grid; grid-template-columns: repeat(3, 1fr); gap: 12px; margin-bottom: 24px; }
.stat-card { background: var(--bg-card); border: 1px solid var(--border); border-radius: 10px; padding: 16px; text-align: center; }
.stat-card.highlight { border-color: var(--brand); background: var(--brand-softer); }
.stat-val { font-size: 24px; font-weight: 700; color: var(--text); }
.stat-card.highlight .stat-val { color: var(--brand); }
.stat-label { font-size: 12px; color: var(--text-tertiary); margin-top: 2px; }
.section-title { font-size: 15px; font-weight: 600; color: var(--text); margin-bottom: 12px; }
.app-card { display: flex; align-items: center; gap: 14px; padding: 14px 16px; background: var(--bg-card); border: 1.5px solid var(--brand); border-radius: 10px; box-shadow: 0 0 0 3px var(--brand-soft); }
.app-icon { font-size: 24px; }
.app-info { flex: 1; }
.app-name { font-size: 14px; font-weight: 600; color: var(--text); }
.app-code { font-size: 12px; color: var(--text-tertiary); font-family: var(--font-mono); }
.app-badge { font-size: 11px; font-weight: 600; color: var(--success); background: var(--success-bg); padding: 2px 10px; border-radius: 12px; }
</style>
