<template>
  <div class="mock-screen approval-screen">
    <div class="mock-topbar">
      <div class="mock-breadcrumb">审批中心</div>
      <div class="mock-user">👤 小黄</div>
    </div>
    <div class="mock-content">
      <h2 class="mock-title">📬 审批中心</h2>

      <div class="section-card">
        <div class="section-label">待我审批</div>
        <div class="approval-item">
          <div class="a-header">
            <span class="a-type">📋 能力包申请</span>
            <span class="a-time">2 分钟前</span>
          </div>
          <div class="a-body">
            <div class="a-row"><span class="a-key">申请人</span><span class="a-val">👤 小红</span></div>
            <div class="a-row"><span class="a-key">授权主体</span><span class="a-val">👤 小红（人）+ 🔌 小红的数据分析（程序）</span></div>
            <div class="a-row"><span class="a-key">能力包</span><span class="a-val">📡 主机监控 — 只读监控</span></div>
            <div class="a-row"><span class="a-key">接口</span><span class="a-val mono">host:list, host:read</span></div>
            <div class="a-row"><span class="a-key">理由</span><span class="a-val">需要读取生产环境主机</span></div>
          </div>
          <div class="a-actions">
            <button class="btn-reject">❌ 拒绝</button>
            <button class="btn-approve">✅ 审批通过</button>
          </div>
        </div>
      </div>

      <div class="result-banner success">
        <span>🎉</span>
        <span>审批通过！策略立即生效，小红已获得「主机监控 - 只读」权限</span>
      </div>

      <div class="note-banner">
        <div class="note-title">💡 演示说明</div>
        <div class="note-text">在生产环境中，审批工单会发送至外部工单平台（如 Jira / ServiceNow），经多级审批后自动回执状态并触发策略下发。此处为演示完整性，内置了简化的审批闭环。</div>
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
.approval-item { border: 1px solid var(--brand); border-radius: 10px; overflow: hidden; }
.a-header { display: flex; justify-content: space-between; align-items: center; padding: 12px 16px; background: var(--brand-softer); border-bottom: 1px solid var(--border); }
.a-type { font-size: 14px; font-weight: 600; color: var(--text); }
.a-time { font-size: 12px; color: var(--text-tertiary); }
.a-body { padding: 14px 16px; }
.a-row { display: flex; gap: 12px; padding: 6px 0; font-size: 13px; }
.a-key { color: var(--text-tertiary); min-width: 70px; }
.a-val { color: var(--text); font-weight: 500; }
.a-val.mono { font-family: var(--font-mono); font-size: 12px; }
.a-actions { display: flex; gap: 10px; padding: 12px 16px; border-top: 1px solid var(--border); justify-content: flex-end; }
.btn-reject { padding: 7px 16px; border: 1px solid var(--danger); border-radius: 6px; background: transparent; color: var(--danger); font-size: 13px; cursor: pointer; }
.btn-approve { padding: 7px 16px; border: none; border-radius: 6px; background: var(--success); color: #fff; font-size: 13px; font-weight: 600; cursor: pointer; }
.result-banner { display: flex; align-items: center; gap: 8px; padding: 14px 18px; border-radius: 10px; font-size: 14px; font-weight: 600; margin-top: 14px; }
.result-banner.success { background: var(--success-bg); color: var(--success); border: 1px solid var(--success); }
.note-banner { margin-top: 14px; padding: 14px 18px; background: var(--info-bg); border: 1px solid var(--info); border-radius: 10px; }
.note-title { font-size: 13px; font-weight: 600; color: var(--info); margin-bottom: 4px; }
.note-text { font-size: 12px; color: var(--text-secondary); line-height: 1.6; }
</style>
