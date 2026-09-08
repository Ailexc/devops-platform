<template>
  <div class="mock-screen status-screen">
    <div class="mock-topbar">
      <div class="mock-breadcrumb">授权管理</div>
      <div class="mock-user">👤 小黄</div>
    </div>
    <div class="mock-content">
      <h2 class="mock-title">📊 授权管理 · 状态确认</h2>

      <div class="section-card">
        <div class="section-label">预设列表</div>
        <table class="mock-table">
          <thead>
            <tr><th>预设名称</th><th>接口数</th><th>状态</th><th>操作</th></tr>
          </thead>
          <tbody>
            <tr>
              <td><strong>只读监控</strong></td>
              <td>2</td>
              <td><span class="tag published">✅ 已上架</span></td>
              <td><button class="btn-offline">下架</button></td>
            </tr>
            <tr>
              <td>完整监控</td>
              <td>3</td>
              <td><span class="tag draft">草稿</span></td>
              <td><button class="btn-publish-sm">🚀 上架</button></td>
            </tr>
          </tbody>
        </table>
      </div>

      <div class="result-banner success">
        <span class="result-icon">🎉</span>
        <span>预设「只读监控」已成功上架！能力市场已可见。</span>
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
.mock-table { width: 100%; border-collapse: collapse; font-size: 13px; }
.mock-table th { text-align: left; padding: 8px 12px; color: var(--text-tertiary); font-weight: 500; border-bottom: 1px solid var(--border); }
.mock-table td { padding: 10px 12px; border-bottom: 1px solid var(--border); color: var(--text); }
.tag { font-size: 11px; font-weight: 600; padding: 2px 10px; border-radius: 12px; }
.tag.published { color: var(--success); background: var(--success-bg); }
.tag.draft { color: var(--warning); background: var(--warning-bg); }
.btn-offline { padding: 5px 12px; border: 1px solid var(--danger); border-radius: 6px; background: transparent; color: var(--danger); font-size: 12px; cursor: pointer; }
.btn-publish-sm { padding: 5px 12px; border: 1px solid var(--brand); border-radius: 6px; background: var(--brand); color: #fff; font-size: 12px; cursor: pointer; }
.result-banner { display: flex; align-items: center; gap: 10px; padding: 14px 20px; border-radius: 10px; font-size: 14px; font-weight: 600; margin-top: 14px; }
.result-banner.success { background: var(--success-bg); color: var(--success); border: 1px solid var(--success); }
.result-icon { font-size: 20px; }
</style>
