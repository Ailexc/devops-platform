<template>
  <div class="mock-screen preset-screen">
    <div class="mock-topbar">
      <div class="mock-breadcrumb">应用管理 / 小黄的监控服务 / 主机监控 / <b>只读监控</b></div>
      <div class="mock-user">👤 小黄</div>
    </div>
    <div class="mock-content">
      <h2 class="mock-title">🔖 只读监控 · 预设配置</h2>

      <div class="section-card">
        <div class="section-label">基础信息</div>
        <div class="form-row"><span class="key">预设名称</span><span class="val">只读监控</span></div>
        <div class="form-row"><span class="key">状态</span><span class="tag draft">草稿</span></div>
        <div class="form-row"><span class="key">包含接口</span><span class="val">host:list, host:read</span></div>
      </div>

      <div class="section-card">
        <div class="section-label">👥 可申请范围</div>
        <div class="scope-grid">
          <div class="scope-item">
            <div class="scope-icon">🏢</div>
            <div class="scope-info">
              <div class="scope-type">按组织</div>
              <div class="scope-val">研发中心、运维中心</div>
            </div>
            <span class="scope-check">✅</span>
          </div>
          <div class="scope-item">
            <div class="scope-icon">👤</div>
            <div class="scope-info">
              <div class="scope-type">按人员</div>
              <div class="scope-val">admin（管理员）</div>
            </div>
            <span class="scope-check">✅</span>
          </div>
          <div class="scope-item">
            <div class="scope-icon">👥</div>
            <div class="scope-info">
              <div class="scope-type">自建组</div>
              <div class="scope-val">未配置</div>
            </div>
            <span class="scope-off">⬜</span>
          </div>
        </div>
      </div>

      <div class="section-card">
        <div class="section-label">🔐 数据级控制</div>
        <div class="data-row">
          <span class="data-label">数据模型</span>
          <span class="data-val">host（主机）</span>
        </div>
        <div class="data-row">
          <span class="data-label">范围</span>
          <span class="data-val">仅生产环境（env == "prod"）</span>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.mock-screen { width: 100%; flex: 1; min-height: 0; display: flex; flex-direction: column; background: var(--bg); }
.mock-topbar { display: flex; justify-content: space-between; align-items: center; padding: 12px 20px; background: var(--bg-card); border-bottom: 1px solid var(--border); font-size: 13px; color: var(--text-secondary); }
.mock-user { font-weight: 500; }
.mock-content { flex: 1; padding: 24px; overflow: auto; }
.mock-title { font-size: 18px; font-weight: 700; color: var(--text); margin-bottom: 20px; }
.section-card { background: var(--bg-card); border: 1px solid var(--border); border-radius: 10px; padding: 16px; margin-bottom: 14px; }
.section-label { font-size: 13px; font-weight: 600; color: var(--text); margin-bottom: 12px; }
.form-row { display: flex; align-items: center; padding: 6px 0; font-size: 13px; gap: 12px; }
.key { color: var(--text-tertiary); min-width: 70px; }
.val { color: var(--text); font-weight: 500; }
.tag { font-size: 11px; font-weight: 600; padding: 2px 10px; border-radius: 12px; }
.tag.draft { color: var(--warning); background: var(--warning-bg); }
.scope-grid { display: flex; flex-direction: column; gap: 10px; }
.scope-item { display: flex; align-items: center; gap: 12px; padding: 10px 14px; border: 1px solid var(--border); border-radius: 8px; }
.scope-icon { font-size: 20px; }
.scope-info { flex: 1; }
.scope-type { font-size: 12px; color: var(--text-tertiary); }
.scope-val { font-size: 13px; font-weight: 500; color: var(--text); }
.scope-check { color: var(--success); }
.scope-off { color: var(--text-tertiary); }
.data-row { display: flex; align-items: center; padding: 6px 0; font-size: 13px; gap: 12px; }
.data-label { color: var(--text-tertiary); min-width: 70px; }
.data-val { color: var(--text); font-weight: 500; font-family: var(--font-mono); font-size: 12px; }
</style>
