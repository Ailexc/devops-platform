<template>
  <div class="mock-screen switch-screen">
    <div class="switch-content">
      <div class="switch-visual">
        <div class="switch-from">
          <div class="switch-avatar red">红</div>
          <div class="switch-name">小红</div>
          <div class="switch-role">权限申请者</div>
        </div>
        <div class="switch-arrow">
          <div class="arrow-line"></div>
          <div class="arrow-icon">→</div>
          <div class="arrow-line"></div>
        </div>
        <div class="switch-to">
          <div class="switch-avatar blue">黄</div>
          <div class="switch-name">小黄</div>
          <div class="switch-role">应用 Owner</div>
        </div>
      </div>

      <div class="switch-msg">
        <div class="msg-icon">🔄</div>
        <div class="msg-text">切换到小黄视角</div>
        <div class="msg-sub">进入审批中心，查看待审批工单</div>
      </div>

      <div class="pending-card">
        <div class="pending-header">
          <span class="pending-title">📬 审批中心</span>
          <span class="pending-count">1 条待审批</span>
        </div>
        <div class="pending-item">
          <div class="pending-badge">NEW</div>
          <div class="pending-info">
            <div class="pending-name">小红 申请「主机监控 - 只读监控」</div>
            <div class="pending-meta">双主体：小红（人）+ 小红的数据分析（程序）· 2 分钟前</div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.mock-screen { width: 100%; flex: 1; min-height: 0; display: flex; align-items: center; justify-content: center; background: linear-gradient(135deg, #f8fafc 0%, var(--brand-softer) 100%); }
.switch-content { text-align: center; }
.switch-visual { display: flex; align-items: center; gap: 24px; margin-bottom: 28px; }
.switch-from, .switch-to { display: flex; flex-direction: column; align-items: center; gap: 6px; }
.switch-avatar { width: 56px; height: 56px; border-radius: 50%; color: #fff; display: flex; align-items: center; justify-content: center; font-size: 22px; font-weight: 700; }
.switch-avatar.red { background: #dc2626; }
.switch-avatar.blue { background: var(--brand); }
.switch-name { font-size: 16px; font-weight: 600; color: var(--text); }
.switch-role { font-size: 12px; color: var(--text-tertiary); }
.switch-arrow { display: flex; align-items: center; gap: 8px; }
.arrow-line { width: 40px; height: 2px; background: var(--brand); }
.arrow-icon { font-size: 20px; color: var(--brand); font-weight: 700; }
.switch-msg { margin-bottom: 24px; }
.msg-icon { font-size: 28px; margin-bottom: 6px; }
.msg-text { font-size: 16px; font-weight: 600; color: var(--text); }
.msg-sub { font-size: 13px; color: var(--text-secondary); margin-top: 4px; }
.pending-card { background: var(--bg-card); border: 1px solid var(--border); border-radius: 10px; padding: 16px; max-width: 40%; text-align: left; box-shadow: var(--shadow-md); }
.pending-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px; }
.pending-title { font-size: 14px; font-weight: 600; color: var(--text); }
.pending-count { font-size: 12px; color: var(--brand); font-weight: 600; background: var(--brand-soft); padding: 2px 10px; border-radius: 10px; }
.pending-item { display: flex; align-items: center; gap: 10px; padding: 10px; background: var(--brand-softer); border: 1px solid var(--brand); border-radius: 8px; }
.pending-badge { font-size: 10px; font-weight: 700; color: #fff; background: var(--danger); padding: 2px 6px; border-radius: 4px; flex-shrink: 0; }
.pending-name { font-size: 13px; font-weight: 600; color: var(--text); }
.pending-meta { font-size: 11px; color: var(--text-tertiary); margin-top: 2px; }
</style>
