<template>
  <div class="mock-screen">
    <div class="mock-topbar"><div class="mock-breadcrumb">系统观测 / <b>决策缓存工作台</b></div><div class="mock-user">👤 admin</div></div>
    <div class="mock-content">
      <h2 class="mock-title">🗄️ 决策缓存工作台</h2>
      <p class="mock-sub">Redis 决策缓存（authz:dec:*）—— 策略变更不生效时的首要排查点</p>

      <div class="stats-grid">
        <div class="stat-card"><div class="sv">2</div><div class="sl">决策缓存键</div></div>
        <div class="stat-card"><div class="sv">1</div><div class="sl">策略快照键</div></div>
        <div class="stat-card"><div class="sv">461</div><div class="sl">累计决策</div></div>
        <div class="stat-card"><div class="sv green">2.6%</div><div class="sl">缓存命中率</div></div>
      </div>

      <div class="toolbar">
        <span class="tb-tip">决策缓存 TTL 内命中直接放行；策略发布/变更会全量失效。若修改策略后仍走旧结果，可一键清理。</span>
        <button class="btn-danger">🧹 清空决策缓存</button>
      </div>

      <div class="section-label">缓存键明细（值格式：1|pids = allow / 0| = deny）</div>
      <div class="section-card">
        <table class="mock-table">
          <thead><tr><th>缓存键</th><th>值</th><th>剩余 TTL</th><th>判定</th></tr></thead>
          <tbody>
            <tr>
              <td class="mono">authz:dec:u:3:cmdb:cmdb:host:create</td>
              <td class="mono">0|</td>
              <td class="mono">52s</td>
              <td><span class="tag amber">DENY</span></td>
            </tr>
            <tr>
              <td class="mono">authz:dec:u:2:cmdb:cmdb:host:read</td>
              <td class="mono">1|1,33,24,85,gp:53</td>
              <td class="mono">52s</td>
              <td><span class="tag ok">ALLOW</span></td>
            </tr>
          </tbody>
        </table>
      </div>

      <div class="key-point"><span>💡</span><span>决策缓存是性能与一致性的平衡点：命中直接放行（亚毫秒），策略发布时按 app 全量失效，保证策略变更即时生效。</span></div>
    </div>
  </div>
</template>
<style scoped>
.mock-screen { width: 100%; flex: 1; min-height: 0; display: flex; flex-direction: column; background: var(--bg); }
.mock-topbar { display: flex; justify-content: space-between; align-items: center; padding: 12px 20px; background: var(--bg-card); border-bottom: 1px solid var(--border); font-size: 13px; color: var(--text-secondary); }
.mock-user { font-weight: 500; }
.mock-content { flex: 1; padding: 18px 22px; overflow: auto; }
.mock-title { font-size: 18px; font-weight: 700; color: var(--text); margin-bottom: 2px; }
.mock-sub { font-size: 12px; color: var(--text-secondary); margin-bottom: 14px; }
.stats-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 10px; margin-bottom: 14px; }
.stat-card { background: var(--bg-card); border: 1.5px solid var(--border); border-radius: 10px; padding: 14px; text-align: center; }
.sv { font-size: 24px; font-weight: 800; color: var(--text); }
.sv.green { color: var(--success); }
.sl { font-size: 11px; color: var(--text-tertiary); margin-top: 2px; }
.toolbar { display: flex; align-items: center; justify-content: space-between; gap: 12px; padding: 10px 14px; background: var(--bg-card); border: 1px solid var(--border); border-radius: 8px; margin-bottom: 16px; }
.tb-tip { font-size: 11px; color: var(--text-secondary); }
.btn-danger { padding: 6px 14px; border: none; border-radius: 6px; background: var(--danger); color: #fff; font-size: 12px; font-weight: 600; cursor: pointer; }
.section-label { font-size: 11px; font-weight: 600; color: var(--text-secondary); margin-bottom: 6px; }
.section-card { background: var(--bg-card); border: 1px solid var(--border); border-radius: 8px; padding: 8px 12px; margin-bottom: 14px; }
.mock-table { width: 100%; border-collapse: collapse; font-size: 12px; }
.mock-table th { text-align: left; padding: 6px 10px; color: var(--text-tertiary); font-weight: 500; border-bottom: 1px solid var(--border); }
.mock-table td { padding: 8px 10px; border-bottom: 1px solid var(--border); color: var(--text); }
.mono { font-family: var(--font-mono); font-size: 11px; }
.tag { font-size: 10px; font-weight: 600; padding: 1px 8px; border-radius: 10px; }
.tag.ok { color: var(--success); background: var(--success-bg); }
.tag.amber { color: var(--warning); background: var(--warning-bg); }
.key-point { display: flex; gap: 8px; padding: 10px 14px; background: var(--info-bg); border: 1px solid var(--info); border-radius: 8px; font-size: 12px; color: var(--info); line-height: 1.5; }
</style>
