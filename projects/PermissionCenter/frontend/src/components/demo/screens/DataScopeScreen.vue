<template>
  <div class="mock-screen datascope-screen">
    <div class="mock-topbar">
      <div class="mock-breadcrumb">能力市场 / 主机监控 / 选择预设 / 选择主体 / <b>数据范围</b></div>
      <div class="mock-user">👤 小红</div>
    </div>
    <div class="mock-content">
      <h2 class="mock-title">🔐 选择数据范围</h2>
      <p class="mock-sub">指定权限生效的数据范围（精确到实例级别）</p>

      <div class="scope-section">
        <div class="scope-label">按环境</div>
        <div class="scope-chips">
          <span class="chip" v-for="e in envs" :key="e.name" :class="{ selected: e.selected }">{{ e.name }}</span>
        </div>
      </div>

      <div class="scope-section">
        <div class="scope-label">按地域</div>
        <div class="scope-chips">
          <span class="chip" v-for="r in regions" :key="r.name" :class="{ selected: r.selected }">{{ r.name }}</span>
        </div>
      </div>

      <div class="scope-section">
        <div class="scope-label">指定实例（可选）</div>
        <div class="instance-list">
          <div class="instance-item" v-for="inst in instances" :key="inst.name" :class="{ selected: inst.selected }">
            <span class="inst-icon">{{ inst.icon }}</span>
            <div class="inst-info">
              <div class="inst-name">{{ inst.name }}</div>
              <div class="inst-meta">{{ inst.meta }}</div>
            </div>
            <span class="inst-check">{{ inst.selected ? '✅' : '⬜' }}</span>
          </div>
        </div>
      </div>

      <div class="expr-preview">
        <div class="expr-label">生成表达式</div>
        <code class="expr-code">env == "prod" && region in ["cn-north", "cn-south"]</code>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
const envs = [
  { name: '🟢 生产环境 (prod)', selected: true },
  { name: '🟡 预发环境 (staging)', selected: false },
  { name: '🔵 开发环境 (dev)', selected: false },
]
const regions = [
  { name: 'cn-north（华北）', selected: true },
  { name: 'cn-south（华南）', selected: true },
  { name: 'ap-southeast（海外）', selected: false },
]
const instances = [
  { icon: '🖥️', name: 'web-01', meta: 'prod · cn-north · 10.0.1.11', selected: true },
  { icon: '🖥️', name: 'web-02', meta: 'prod · cn-north · 10.0.1.12', selected: true },
  { icon: '🖥️', name: 'db-01', meta: 'prod · cn-south · 10.0.2.21', selected: false },
  { icon: '🖥️', name: 'app-01', meta: 'staging · cn-north · 10.0.3.31', selected: false },
]
</script>

<style scoped>
.mock-screen { width: 100%; flex: 1; min-height: 0; display: flex; flex-direction: column; background: var(--bg); }
.mock-topbar { display: flex; justify-content: space-between; align-items: center; padding: 12px 20px; background: var(--bg-card); border-bottom: 1px solid var(--border); font-size: 13px; color: var(--text-secondary); }
.mock-user { font-weight: 500; }
.mock-content { flex: 1; padding: 24px; overflow: auto; }
.mock-title { font-size: 18px; font-weight: 700; color: var(--text); margin-bottom: 4px; }
.mock-sub { font-size: 13px; color: var(--text-secondary); margin-bottom: 20px; }
.scope-section { background: var(--bg-card); border: 1px solid var(--border); border-radius: 10px; padding: 14px 16px; margin-bottom: 12px; }
.scope-label { font-size: 13px; font-weight: 600; color: var(--text); margin-bottom: 10px; }
.scope-chips { display: flex; gap: 8px; flex-wrap: wrap; }
.chip { font-size: 13px; padding: 6px 14px; border: 1.5px solid var(--border); border-radius: 20px; color: var(--text-secondary); cursor: pointer; transition: all 0.15s; }
.chip.selected { border-color: var(--brand); background: var(--brand-soft); color: var(--brand); font-weight: 600; }
.instance-list { display: flex; flex-direction: column; gap: 8px; }
.instance-item { display: flex; align-items: center; gap: 12px; padding: 10px 14px; border: 1px solid var(--border); border-radius: 8px; transition: all 0.15s; }
.instance-item.selected { border-color: var(--brand); background: var(--brand-softer); }
.inst-icon { font-size: 20px; flex-shrink: 0; }
.inst-info { flex: 1; }
.inst-name { font-size: 13px; font-weight: 600; color: var(--text); font-family: var(--font-mono); }
.inst-meta { font-size: 11px; color: var(--text-tertiary); margin-top: 1px; }
.inst-check { font-size: 16px; flex-shrink: 0; }
.expr-preview { background: #1e293b; border-radius: 8px; padding: 12px 16px; margin-top: 4px; }
.expr-label { font-size: 11px; color: #94a3b8; margin-bottom: 6px; font-weight: 500; }
.expr-code { font-family: var(--font-mono); font-size: 13px; color: #38bdf8; }
</style>
