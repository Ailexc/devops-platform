<template>
  <div class="mock-screen market-screen">
    <div class="mock-topbar">
      <div class="mock-breadcrumb">🏠 工作台 / <b>能力市场</b></div>
      <div class="mock-user">👤 小红</div>
    </div>
    <div class="mock-content">
      <h2 class="mock-title">🏪 能力市场</h2>

      <div class="search-bar">
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="11" cy="11" r="8"/><path d="m21 21-4.35-4.35"/></svg>
        <span class="search-placeholder">搜索能力…</span>
      </div>

      <div class="cap-grid">
        <div class="cap-card" v-for="c in caps" :key="c.name" :class="{ highlight: c.highlight }">
          <div class="cap-header">
            <div class="cap-icon">{{ c.icon }}</div>
            <div class="cap-app">{{ c.app }}</div>
          </div>
          <div class="cap-name">{{ c.name }}</div>
          <div class="cap-desc">{{ c.desc }}</div>
          <div class="cap-tags">
            <span class="tag" v-for="t in c.tags" :key="t">{{ t }}</span>
          </div>
          <div class="cap-footer">
            <span class="preset-count">{{ c.presets }} 个预设</span>
            <button class="btn-apply" v-if="c.highlight">申请 →</button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
const caps = [
  { icon: '📡', app: '小黄的监控服务', name: '主机监控', desc: '主机列表查看与详情读取', tags: ['host', '只读'], presets: 2, highlight: true },
  { icon: '🗃️', app: 'CMDB', name: '主机管理', desc: '主机全生命周期管理', tags: ['host', 'CRUD'], presets: 3, highlight: false },
  { icon: '🎫', app: 'ITSM 工单', name: '工单管理', desc: '工单创建与处理能力', tags: ['ticket', 'CRUD'], presets: 2, highlight: false },
]
</script>

<style scoped>
.mock-screen { width: 100%; flex: 1; min-height: 0; display: flex; flex-direction: column; background: var(--bg); }
.mock-topbar { display: flex; justify-content: space-between; align-items: center; padding: 12px 20px; background: var(--bg-card); border-bottom: 1px solid var(--border); font-size: 13px; color: var(--text-secondary); }
.mock-user { font-weight: 500; }
.mock-content { flex: 1; padding: 24px; overflow: auto; }
.mock-title { font-size: 18px; font-weight: 700; color: var(--text); margin-bottom: 16px; }
.search-bar { display: flex; align-items: center; gap: 8px; padding: 10px 14px; background: var(--bg-card); border: 1px solid var(--border); border-radius: 8px; margin-bottom: 20px; color: var(--text-tertiary); }
.search-placeholder { font-size: 13px; }
.cap-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 14px; }
.cap-card { background: var(--bg-card); border: 1px solid var(--border); border-radius: 10px; padding: 16px; transition: all 0.2s; }
.cap-card.highlight { border-color: var(--brand); box-shadow: 0 0 0 3px var(--brand-soft); }
.cap-header { display: flex; align-items: center; gap: 10px; margin-bottom: 10px; }
.cap-icon { font-size: 24px; }
.cap-app { font-size: 11px; color: var(--text-tertiary); }
.cap-name { font-size: 15px; font-weight: 600; color: var(--text); margin-bottom: 4px; }
.cap-desc { font-size: 12px; color: var(--text-secondary); margin-bottom: 10px; }
.cap-tags { display: flex; gap: 6px; margin-bottom: 12px; }
.tag { font-size: 11px; padding: 2px 8px; border-radius: 10px; background: var(--bg-tertiary); color: var(--text-secondary); }
.cap-footer { display: flex; justify-content: space-between; align-items: center; }
.preset-count { font-size: 12px; color: var(--text-tertiary); }
.btn-apply { padding: 5px 14px; border: none; border-radius: 6px; background: var(--brand); color: #fff; font-size: 12px; font-weight: 600; cursor: pointer; }
</style>
