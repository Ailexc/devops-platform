<template>
  <div class="mock-screen authz-screen">
    <div class="mock-topbar">
      <div class="mock-breadcrumb">应用管理 / 小黄的监控服务 / 主机监控 / <b>授权管理</b></div>
      <div class="mock-user">👤 小黄</div>
    </div>
    <div class="mock-content">
      <h2 class="mock-title">🛡️ 授权管理</h2>

      <div class="section-card">
        <div class="section-label">预设列表</div>
        <table class="mock-table">
          <thead>
            <tr><th>预设名称</th><th>接口数</th><th>状态</th><th>操作</th></tr>
          </thead>
          <tbody>
            <tr>
              <td>只读监控</td>
              <td>2</td>
              <td><span class="tag draft">草稿</span></td>
              <td>
                <button class="btn-publish">🚀 上架</button>
              </td>
            </tr>
            <tr>
              <td>完整监控</td>
              <td>3</td>
              <td><span class="tag draft">草稿</span></td>
              <td>
                <button class="btn-publish">🚀 上架</button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <div class="section-card">
        <div class="section-label">📊 授权概况（四维统计）</div>
        <div class="stats-grid">
          <div class="mini-stat"><div class="ms-val">0</div><div class="ms-label">👤 用户</div></div>
          <div class="mini-stat"><div class="ms-val">0</div><div class="ms-label">🏢 组织</div></div>
          <div class="mini-stat"><div class="ms-val">0</div><div class="ms-label">👥 自建组</div></div>
          <div class="mini-stat"><div class="ms-val">0</div><div class="ms-label">🔌 程序</div></div>
        </div>
        <div class="stats-note">暂无授权 —— 预设上架后，用户申请通过即在此按 用户/组织/自建组/程序 四维统计</div>
      </div>

      <div class="publish-dialog">
        <div class="dialog-title">确认上架「只读监控」预设？</div>
        <div class="dialog-desc">上架后该预设将出现在能力市场，其他用户可申请此权限。</div>
        <div class="dialog-actions">
          <button class="btn-cancel">取消</button>
          <button class="btn-confirm">✅ 确认上架</button>
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
.mock-table { width: 100%; border-collapse: collapse; font-size: 13px; }
.mock-table th { text-align: left; padding: 8px 12px; color: var(--text-tertiary); font-weight: 500; border-bottom: 1px solid var(--border); }
.mock-table td { padding: 10px 12px; border-bottom: 1px solid var(--border); color: var(--text); }
.tag { font-size: 11px; font-weight: 600; padding: 2px 10px; border-radius: 12px; }
.tag.draft { color: var(--warning); background: var(--warning-bg); }
.btn-publish { padding: 5px 14px; border: 1px solid var(--brand); border-radius: 6px; background: var(--brand); color: #fff; font-size: 12px; font-weight: 600; cursor: pointer; }
.stats-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 10px; }
.mini-stat { text-align: center; padding: 12px 8px; background: var(--bg-secondary); border-radius: 8px; }
.ms-val { font-size: 22px; font-weight: 700; color: var(--text); }
.ms-label { font-size: 12px; color: var(--text-tertiary); margin-top: 2px; }
.stats-note { margin-top: 8px; font-size: 11px; color: var(--text-tertiary); }
.publish-dialog { background: var(--bg-card); border: 2px solid var(--brand); border-radius: 12px; padding: 20px; margin-top: 14px; box-shadow: var(--shadow-lg); }
.dialog-title { font-size: 15px; font-weight: 600; color: var(--text); margin-bottom: 8px; }
.dialog-desc { font-size: 13px; color: var(--text-secondary); margin-bottom: 16px; }
.dialog-actions { display: flex; gap: 10px; justify-content: flex-end; }
.btn-cancel { padding: 8px 16px; border: 1px solid var(--border); border-radius: 6px; background: var(--bg-card); color: var(--text-secondary); font-size: 13px; cursor: pointer; }
.btn-confirm { padding: 8px 16px; border: none; border-radius: 6px; background: var(--success); color: #fff; font-size: 13px; font-weight: 600; cursor: pointer; }
</style>
