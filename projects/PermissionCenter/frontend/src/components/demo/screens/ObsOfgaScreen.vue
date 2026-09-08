<template>
  <div class="mock-screen">
    <div class="mock-topbar"><div class="mock-breadcrumb">系统观测 / <b>数据面图谱（OpenFGA）</b></div><div class="mock-user">👤 admin</div></div>
    <div class="mock-content">
      <h2 class="mock-title">🔗 数据面图谱（OpenFGA）</h2>
      <p class="mock-sub">实例级授权关系引擎（CNCF/Zanzibar）—— 数据级授权的关系物化全貌</p>

      <div class="stats-grid">
        <div class="stat-card"><div class="sv">0</div><div class="sl">关系元组</div></div>
        <div class="stat-card"><div class="sv">3</div><div class="sl">资源类型</div></div>
        <div class="stat-card"><div class="sv mono sm">01KZ5CTJCG2S</div><div class="sl">模型 ID</div></div>
      </div>

      <div class="section-label">授权模型（type 定义）</div>
      <div class="section-card model">
        <div class="type-node core"><span class="t-name">user</span><span class="t-rel">主体</span></div>
        <div class="type-node core"><span class="t-name">service</span><span class="t-rel">程序主体</span></div>
        <div class="type-node group"><span class="t-name">group</span><span class="t-rel">member</span></div>
        <div class="type-node res" v-for="r in resources" :key="r">
          <span class="t-name">{{ r }}</span>
          <span class="t-rel">owner · reader · writer</span>
        </div>
      </div>

      <div class="section-label">关系元组（按资源类型分组）</div>
      <div class="section-card">
        <div class="empty">暂无关系元组 —— 数据级授权（check-instance）通过时写入实例级关系，此处展示全部物化关系</div>
      </div>

      <div class="key-point"><span>💡</span><span>OpenFGA 负责「数据级」授权：动作级（Casbin）通过后，再按实例过滤数据范围，如 bob can_read host-01。关系物化后可用 ReadTypeTuples 全量观测。</span></div>
    </div>
  </div>
</template>
<script setup lang="ts">
const resources = ['host', 'network', 'disk']
</script>
<style scoped>
.mock-screen { width: 100%; flex: 1; min-height: 0; display: flex; flex-direction: column; background: var(--bg); }
.mock-topbar { display: flex; justify-content: space-between; align-items: center; padding: 12px 20px; background: var(--bg-card); border-bottom: 1px solid var(--border); font-size: 13px; color: var(--text-secondary); }
.mock-user { font-weight: 500; }
.mock-content { flex: 1; padding: 18px 22px; overflow: auto; }
.mock-title { font-size: 18px; font-weight: 700; color: var(--text); margin-bottom: 2px; }
.mock-sub { font-size: 12px; color: var(--text-secondary); margin-bottom: 14px; }
.stats-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 10px; margin-bottom: 16px; }
.stat-card { background: var(--bg-card); border: 1.5px solid var(--border); border-radius: 10px; padding: 14px; text-align: center; }
.sv { font-size: 24px; font-weight: 800; color: var(--text); }
.sv.mono { font-family: var(--font-mono); font-size: 15px; font-weight: 700; }
.sv.sm { font-size: 13px; }
.sl { font-size: 11px; color: var(--text-tertiary); margin-top: 2px; }
.section-label { font-size: 11px; font-weight: 600; color: var(--text-secondary); margin-bottom: 6px; }
.section-card { background: var(--bg-card); border: 1px solid var(--border); border-radius: 8px; padding: 12px 14px; margin-bottom: 14px; }
.model { display: flex; flex-wrap: wrap; gap: 10px; }
.type-node { display: flex; align-items: center; gap: 8px; padding: 8px 14px; border-radius: 8px; border: 1px solid var(--border); font-size: 13px; }
.type-node.core { background: var(--info-bg); border-color: var(--info); }
.type-node.group { background: var(--purple-bg); border-color: var(--purple); }
.type-node.res { background: var(--success-bg); border-color: var(--success); }
.t-name { font-weight: 700; color: var(--text); }
.t-rel { font-size: 11px; color: var(--text-tertiary); }
.empty { padding: 20px; text-align: center; color: var(--text-tertiary); font-size: 12px; }
.key-point { display: flex; gap: 8px; padding: 10px 14px; background: var(--info-bg); border: 1px solid var(--info); border-radius: 8px; font-size: 12px; color: var(--info); line-height: 1.5; }
</style>
