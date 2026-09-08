<template>
  <div class="mock-screen">
    <div class="mock-topbar"><div class="mock-breadcrumb">系统观测 / <b>决策日志</b></div><div class="mock-user">👤 admin</div></div>
    <div class="mock-content">
      <h2 class="mock-title">📊 决策日志</h2>
      <p class="mock-sub">每条网关请求自动生成审计日志，完整留痕</p>
      <table class="mock-table">
        <thead><tr><th>时间</th><th>TraceID</th><th>用户</th><th>操作</th><th>决策</th><th>来源</th></tr></thead>
        <tbody>
          <tr><td>10:32:15</td><td class="mono">a1b2c3d4</td><td>bob</td><td class="mono">GET /hosts</td><td><span class="tag allow">ALLOW</span></td><td>组权限+数据策略</td></tr>
          <tr><td>10:32:18</td><td class="mono">e5f6g7h8</td><td>bob</td><td class="mono">POST /hosts</td><td><span class="tag deny">DENY</span></td><td>无 host:create</td></tr>
          <tr><td>10:32:20</td><td class="mono">i9j0k1l2</td><td>alice</td><td class="mono">GET /hosts</td><td><span class="tag allow">ALLOW</span></td><td>应用 Owner</td></tr>
          <tr><td>10:32:22</td><td class="mono">m3n4o5p6</td><td>client:cloud-mgmt</td><td class="mono">GET /hosts</td><td><span class="tag allow">ALLOW</span></td><td>OpenFGA 条件</td></tr>
        </tbody>
      </table>
      <div class="key-point"><span>💡</span><span>审计日志包含 TraceID，可与鉴权链路追踪页面联动，实现从网关请求到决策的全链路溯源。</span></div>
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
.mock-table { width: 100%; border-collapse: collapse; font-size: 12px; background: var(--bg-card); border-radius: 10px; overflow: hidden; border: 1px solid var(--border); }
.mock-table th { text-align: left; padding: 7px 10px; color: var(--text-tertiary); font-weight: 500; border-bottom: 1px solid var(--border); background: var(--bg-secondary); }
.mock-table td { padding: 7px 10px; border-bottom: 1px solid var(--border); color: var(--text); }
.mono { font-family: var(--font-mono); font-size: 11px; }
.tag { font-size: 10px; font-weight: 600; padding: 2px 8px; border-radius: 10px; }
.tag.allow { color: var(--success); background: var(--success-bg); }
.tag.deny { color: var(--danger); background: var(--danger-bg); }
.key-point { display: flex; gap: 8px; padding: 10px 14px; background: var(--info-bg); border: 1px solid var(--info); border-radius: 8px; font-size: 12px; color: var(--info); line-height: 1.5; margin-top: 14px; }
</style>
