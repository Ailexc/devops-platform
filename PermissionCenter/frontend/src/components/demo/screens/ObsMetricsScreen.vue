<template>
  <div class="mock-screen">
    <div class="mock-topbar"><div class="mock-breadcrumb">系统观测 / <b>鉴权指标面板</b></div><div class="mock-user">👤 admin</div></div>
    <div class="mock-content">
      <h2 class="mock-title">📈 鉴权指标面板</h2>
      <p class="mock-sub">从决策日志聚合：决策量 / 允许拒绝 / 缓存命中 / 延迟 / 趋势 / Top 动作</p>

      <div class="stats-grid">
        <div class="stat-card"><div class="sv">461</div><div class="sl">累计决策</div></div>
        <div class="stat-card green"><div class="sv">334</div><div class="sl">允许</div></div>
        <div class="stat-card red"><div class="sv">127</div><div class="sl">拒绝</div></div>
        <div class="stat-card"><div class="sv">2.6%</div><div class="sl">缓存命中率</div></div>
        <div class="stat-card violet"><div class="sv">17ms</div><div class="sl">P95 延迟</div></div>
      </div>

      <div class="mini-grid">
        <div class="mini"><span class="mk">P50</span><span class="mv">1ms</span></div>
        <div class="mini"><span class="mk">P90</span><span class="mv">10ms</span></div>
        <div class="mini"><span class="mk">来源 · cache</span><span class="mv">12</span></div>
        <div class="mini"><span class="mk">来源 · remote</span><span class="mv">449</span></div>
      </div>

      <div class="section-label">最近 24H 决策趋势</div>
      <div class="section-card">
        <div class="trend">
          <div class="bar-col" v-for="b in bars" :key="b.h">
            <div class="bar-stack" :style="{ height: b.h }">
              <div class="bar-allow" :style="{ height: b.a + '%' }"></div>
              <div class="bar-deny" :style="{ height: b.d + '%' }"></div>
            </div>
            <div class="bar-hour">{{ b.hour }}</div>
          </div>
        </div>
        <div class="legend"><span class="lg allow">允许</span><span class="lg deny">拒绝</span></div>
      </div>

      <div class="section-label">TOP 被访问权限点</div>
      <div class="section-card">
        <div class="top-row" v-for="(t, i) in topActions" :key="t.action">
          <span class="top-idx">{{ i + 1 }}</span>
          <span class="top-name mono">{{ t.action }}</span>
          <div class="top-bar-bg"><div class="top-bar" :style="{ width: t.w }"></div></div>
          <span class="top-count">{{ t.count }} 次</span>
        </div>
      </div>
    </div>
  </div>
</template>
<script setup lang="ts">
const bars = [
  { h: '64px', a: 73, d: 27, hour: '08' },
  { h: '64px', a: 73, d: 27, hour: '09' },
  { h: '96px', a: 73, d: 27, hour: '20' },
  { h: '104px', a: 73, d: 27, hour: '06' },
  { h: '96px', a: 64, d: 36, hour: '07' },
]
const topActions = [
  { action: 'cmdb:host:read', count: 243, w: '100%' },
  { action: 'cmdb:host:create', count: 99, w: '41%' },
  { action: 'cmdb:host:list', count: 73, w: '30%' },
  { action: 'cmdb:host:update', count: 31, w: '13%' },
  { action: 'cmdb:model:list', count: 8, w: '4%' },
]
</script>
<style scoped>
.mock-screen { width: 100%; flex: 1; min-height: 0; display: flex; flex-direction: column; background: var(--bg); }
.mock-topbar { display: flex; justify-content: space-between; align-items: center; padding: 12px 20px; background: var(--bg-card); border-bottom: 1px solid var(--border); font-size: 13px; color: var(--text-secondary); }
.mock-user { font-weight: 500; }
.mock-content { flex: 1; padding: 18px 22px; overflow: auto; }
.mock-title { font-size: 18px; font-weight: 700; color: var(--text); margin-bottom: 2px; }
.mock-sub { font-size: 12px; color: var(--text-secondary); margin-bottom: 14px; }
.stats-grid { display: grid; grid-template-columns: repeat(5, 1fr); gap: 10px; margin-bottom: 10px; }
.stat-card { background: var(--bg-card); border: 1.5px solid var(--border); border-radius: 10px; padding: 12px; text-align: center; }
.stat-card.green { border-color: var(--success); }
.stat-card.red { border-color: var(--danger); }
.stat-card.violet { border-color: var(--purple); }
.sv { font-size: 22px; font-weight: 800; color: var(--text); }
.stat-card.green .sv { color: var(--success); }
.stat-card.red .sv { color: var(--danger); }
.stat-card.violet .sv { color: var(--purple); }
.sl { font-size: 10px; color: var(--text-tertiary); margin-top: 2px; }
.mini-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 10px; margin-bottom: 16px; }
.mini { display: flex; justify-content: space-between; align-items: center; padding: 8px 12px; background: var(--bg-card); border: 1px solid var(--border); border-radius: 8px; }
.mk { font-size: 11px; color: var(--text-tertiary); }
.mv { font-size: 13px; font-weight: 700; color: var(--text); font-family: var(--font-mono); }
.section-label { font-size: 11px; font-weight: 600; color: var(--text-secondary); margin-bottom: 6px; }
.section-card { background: var(--bg-card); border: 1px solid var(--border); border-radius: 8px; padding: 12px 14px; margin-bottom: 14px; }
.trend { display: flex; align-items: flex-end; gap: 18px; height: 120px; padding: 0 8px; }
.bar-col { display: flex; flex-direction: column; align-items: center; gap: 4px; flex: 1; }
.bar-stack { width: 26px; border-radius: 4px; overflow: hidden; display: flex; flex-direction: column; justify-content: flex-end; background: var(--bg-tertiary); }
.bar-allow { background: var(--success); width: 100%; }
.bar-deny { background: var(--danger); width: 100%; }
.bar-hour { font-size: 10px; color: var(--text-tertiary); font-family: var(--font-mono); }
.legend { display: flex; gap: 14px; margin-top: 8px; font-size: 11px; color: var(--text-secondary); }
.lg::before { content: ''; display: inline-block; width: 10px; height: 10px; border-radius: 2px; margin-right: 4px; vertical-align: -1px; }
.lg.allow::before { background: var(--success); }
.lg.deny::before { background: var(--danger); }
.top-row { display: flex; align-items: center; gap: 10px; padding: 5px 0; font-size: 12px; }
.top-idx { width: 18px; height: 18px; border-radius: 50%; background: var(--bg-tertiary); color: var(--text-tertiary); display: flex; align-items: center; justify-content: center; font-size: 10px; font-weight: 700; flex-shrink: 0; }
.top-name { flex: 0 0 160px; color: var(--text); }
.top-bar-bg { flex: 1; height: 8px; background: var(--bg-tertiary); border-radius: 4px; overflow: hidden; }
.top-bar { height: 100%; background: var(--brand); border-radius: 4px; }
.top-count { font-size: 11px; color: var(--text-tertiary); font-family: var(--font-mono); }
.mono { font-family: var(--font-mono); }
</style>
