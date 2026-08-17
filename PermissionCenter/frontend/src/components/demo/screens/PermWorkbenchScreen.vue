<template>
  <div class="mock-screen">
    <div class="mock-topbar"><div class="mock-breadcrumb">🏠 工作台</div><div class="mock-user">👤 bob</div></div>
    <div class="mock-content">
      <h2 class="mock-title">工作台</h2>
      <p class="mock-sub">以「我」为中心 —— 权限、待办、应用与快捷入口</p>

      <div class="identity-card">
        <div class="id-avatar">B</div>
        <div>
          <div class="id-name">鲍勃（bob）</div>
          <div class="id-sub">总公司 → 研发中心 → 研发一部 · 成员</div>
        </div>
      </div>

      <div class="stats-row">
        <div class="stat-card blue" @click="">
          <div class="stat-val">2</div>
          <div class="stat-label">🏢 组织权限</div>
          <div class="stat-desc">来自组织树继承</div>
        </div>
        <div class="stat-card green">
          <div class="stat-val">22</div>
          <div class="stat-label">👤 个人权限</div>
          <div class="stat-desc">个人申请获得</div>
        </div>
        <div class="stat-card amber">
          <div class="stat-val">2</div>
          <div class="stat-label">👥 自建组权限</div>
          <div class="stat-desc">自建组成员</div>
        </div>
        <div class="stat-card violet">
          <div class="stat-val">0</div>
          <div class="stat-label">📦 负责应用</div>
          <div class="stat-desc">应用 Owner</div>
        </div>
      </div>

      <div class="key-point">
        <span>💡</span>
        <span>工作台以四维统计展示权限分布。点击任一卡片进入「我的权限」页面，按三个维度分类查看所有能力包授权。</span>
      </div>
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
.identity-card { display: flex; align-items: center; gap: 12px; padding: 12px 16px; background: var(--brand-soft); border: 1px solid var(--brand); border-radius: 10px; margin-bottom: 14px; cursor: pointer; }
.id-avatar { width: 40px; height: 40px; border-radius: 50%; background: var(--brand); color: #fff; display: flex; align-items: center; justify-content: center; font-weight: 700; font-size: 16px; flex-shrink: 0; }
.id-name { font-size: 15px; font-weight: 600; color: var(--text); }
.id-sub { font-size: 11px; color: var(--text-secondary); margin-top: 1px; }
.stats-row { display: grid; grid-template-columns: repeat(4, 1fr); gap: 10px; margin-bottom: 14px; }
.stat-card { background: var(--bg-card); border: 1.5px solid var(--border); border-radius: 10px; padding: 12px; text-align: center; cursor: pointer; transition: all 0.15s; }
.stat-card.blue { border-color: var(--brand); }
.stat-card.green { border-color: var(--success); }
.stat-card.amber { border-color: var(--warning); }
.stat-card.violet { border-color: var(--purple); }
.stat-val { font-size: 22px; font-weight: 700; color: var(--text); }
.stat-card.blue .stat-val { color: var(--brand); }
.stat-card.green .stat-val { color: var(--success); }
.stat-card.amber .stat-val { color: var(--warning); }
.stat-card.violet .stat-val { color: var(--purple); }
.stat-label { font-size: 12px; font-weight: 600; color: var(--text); margin-top: 2px; }
.stat-desc { font-size: 10px; color: var(--text-tertiary); margin-top: 1px; }
.key-point { display: flex; gap: 8px; padding: 10px 14px; background: var(--info-bg); border: 1px solid var(--info); border-radius: 8px; font-size: 12px; color: var(--info); line-height: 1.5; }
</style>
